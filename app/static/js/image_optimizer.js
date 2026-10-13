/**
 * Client-Side Image Optimizer & Direct Storage Upload
 * Prevents Vercel 413 FUNCTION_PAYLOAD_TOO_LARGE by:
 * 1. Scaling oversized photos to max 1200px and compressing to high-efficiency JPEG.
 * 2. Updating file input using DataTransfer (reducing payload from >5MB down to ~150KB).
 * 3. Pre-uploading directly to the backend storage endpoint (/api/upload-image)
 *    so the main registration form only sends lightweight references.
 */
document.addEventListener('DOMContentLoaded', function () {
  const fileInputs = document.querySelectorAll('input[type="file"][name="image"]');

  fileInputs.forEach(function (input) {
    const form = input.closest('form');
    if (!form) return;

    // Create container for live feedback
    const container = document.createElement('div');
    container.className = 'image-optimizer-feedback mt-2';
    input.parentNode.appendChild(container);

    // Create hidden input to hold direct upload path
    let hiddenInput = form.querySelector('input[name="direct_image_path"]');
    if (!hiddenInput) {
      hiddenInput = document.createElement('input');
      hiddenInput.type = 'hidden';
      hiddenInput.name = 'direct_image_path';
      hiddenInput.id = 'direct_image_path';
      form.appendChild(hiddenInput);
    }

    input.addEventListener('change', function (e) {
      const file = e.target.files && e.target.files[0];
      if (!file) {
        container.innerHTML = '';
        hiddenInput.value = '';
        return;
      }

      // Check if it's an image
      if (!file.type.match(/^image\//i)) {
        return;
      }

      const origSizeMb = (file.size / (1024 * 1024)).toFixed(2);
      container.innerHTML = `
        <div class="d-flex align-items-center gap-2 text-primary small py-1">
          <div class="spinner-border spinner-border-sm text-primary" role="status" aria-hidden="true"></div>
          <span>Optimizing image for fast Vercel upload (${origSizeMb} MB)...</span>
        </div>
      `;

      // Disable submit buttons during processing to prevent premature submit
      const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
      submitButtons.forEach(btn => btn.disabled = true);

      const reader = new FileReader();
      reader.onload = function (readerEvent) {
        const img = new Image();
        img.onload = function () {
          const maxDim = 1200;
          let width = img.width;
          let height = img.height;

          if (width > maxDim || height > maxDim) {
            if (width > height) {
              height = Math.round((height * maxDim) / width);
              width = maxDim;
            } else {
              width = Math.round((width * maxDim) / height);
              height = maxDim;
            }
          }

          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);

          // Compress to JPEG with 0.82 quality
          canvas.toBlob(function (blob) {
            if (!blob) {
              container.innerHTML = '<div class="text-warning small">Optimization skipped, using original.</div>';
              submitButtons.forEach(btn => btn.disabled = false);
              return;
            }

            const optimizedSizeKb = (blob.size / 1024).toFixed(0);
            const optimizedFile = new File([blob], file.name.replace(/\.[^.]+$/, '') + '.jpg', {
              type: 'image/jpeg',
              lastModified: Date.now()
            });

            // Replace input.files using DataTransfer if supported
            try {
              const dt = new DataTransfer();
              dt.items.add(optimizedFile);
              input.files = dt.files;
            } catch (err) {
              console.warn('DataTransfer not supported by browser, fallback to FormData upload.', err);
            }

            container.innerHTML = `
              <div class="alert alert-success py-2 px-3 mb-0 small rounded-3 d-flex flex-wrap align-items-center justify-content-between gap-2">
                <span>
                  <i class="bi bi-check-circle-fill text-success me-1"></i>
                  <strong>Photo Optimized:</strong> ${optimizedSizeKb} KB
                  <span class="text-muted">(reduced from ${origSizeMb} MB)</span>
                </span>
                <span class="badge bg-success-subtle text-success border border-success-subtle" id="upload-status-badge">
                  <i class="bi bi-cloud-arrow-up me-1"></i>Optimized for Vercel
                </span>
              </div>
            `;

            submitButtons.forEach(btn => btn.disabled = false);

            // Background pre-upload to storage endpoint
            const csrfTokenEl = form.querySelector('input[name="csrf_token"]');
            const csrfToken = csrfTokenEl ? csrfTokenEl.value : '';

            const uploadData = new FormData();
            uploadData.append('image', optimizedFile);
            if (csrfToken) {
              uploadData.append('csrf_token', csrfToken);
            }

            fetch('/api/upload-image', {
              method: 'POST',
              body: uploadData
            })
            .then(res => res.json())
            .then(data => {
              if (data && data.success && data.image_path) {
                hiddenInput.value = data.image_path;
                const badge = container.querySelector('#upload-status-badge');
                if (badge) {
                  badge.className = 'badge bg-primary-subtle text-primary border border-primary-subtle';
                  badge.innerHTML = '<i class="bi bi-cloud-check-fill me-1"></i>Direct Storage Ready';
                }
              }
            })
            .catch(err => {
              // Non-blocking: regular form submission with optimized File will proceed
              console.warn('Background direct storage upload failed, will fallback to form payload:', err);
            });

          }, 'image/jpeg', 0.82);
        };
        img.src = readerEvent.target.result;
      };
      reader.readAsDataURL(file);
    });
  });
});
