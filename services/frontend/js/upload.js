/**
 * Image-host front-end logic
 * - Upload via button or drag-&-drop
 * - List uploaded images as cards
 * - Delete images
 */
(() => {
    /* --------------------------------------------------------------------
     *  CONSTANTS
     * ------------------------------------------------------------------ */
    const API_UPLOAD_URL = `${location.origin}/api/upload/`;
    const API_DELETE_URL = (fn) => `${location.origin}/api/upload/${encodeURIComponent(fn)}`;

    const SEL = {
        uploadBtn: '#uploadBtn',
        fileInput: '#fileInput',
        resultInput: '#resultLink',
        copyBtn: '#copyBtn',
        uploadText: '.upload-main-text, .upload-error',
        dropArea: '#dropArea',
        imgSection: '#images-tab',
        imgTabBtn: '.tab[data-tab="images"]',
        imageGallery: '.image-gallery'
    };

    const $ = (s) => document.querySelector(s);

    /**
     * Display status message in upload text area.
     * @param {HTMLElement} el - Element to display message in.
     * @param {string} msg - Message to show.
     * @param {boolean} [isErr=false] - Whether it's an error message.
     */
    const showStatus = (el, msg, isErr = false) => {
        el.classList.toggle('upload-error', isErr);
        el.classList.toggle('upload-main-text', !isErr);
        el.textContent = msg;
    };

    /**
     * Perform API request with Axios.
     * @param {'get'|'post'|'delete'} method - HTTP method.
     * @param {string} url - API endpoint URL.
     * @param {*} [data] - Request body data.
     * @param {object} [cfg={}] - Axios config.
     * @returns {Promise<any>}
     */
    const api = async (method, url, data, cfg = {}) => {
        try {
            return await axios({method, url, data, ...cfg});
        } catch (e) {
            const error = {
                status: e.response?.status ?? null,
                message: e.response?.data?.detail || e.message || 'Unknown error',
            };

            if (method.toLowerCase() === 'get' && url === API_UPLOAD_URL && error.status === 404) {
                return {data: []};
            }

            throw error;
        }
    };

    /**
     * Copy text to clipboard and show feedback
     * @param {string} text - Text to copy
     * @param {HTMLElement} button - Button to show feedback on
     * @param {string} originalText - Button's original text to restore
     */
    const copyToClipboard = async (text, button, originalText) => {
        await navigator.clipboard.writeText(text);
        button.textContent = 'Copied!';
        setTimeout(() => (button.textContent = originalText), 1500);
    };

    /**
     * Initialize upload functionality.
     */
    function initUploader() {
        const uploadBtn = $(SEL.uploadBtn);
        const fileInput = $(SEL.fileInput);
        const resultInput = $(SEL.resultInput);
        const copyBtn = $(SEL.copyBtn);
        const uploadText = $(SEL.uploadText);
        const dropArea = $(SEL.dropArea);

        if (!uploadBtn || !fileInput || !resultInput || !copyBtn || !uploadText || !dropArea) return;

        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
        const maxSize = 1 * 1024 * 1024;

        /**
         * Upload a single file to the server.
         * @param {File} file - File to upload.
         */
        const uploadFile = async (file) => {
            if (!allowedTypes.includes(file.type) || file.size > maxSize) {
                showStatus(uploadText, 'Upload failed: invalid type or size.', true);
                return;
            }
            try {
                const form = new FormData();
                form.append('file', file);
                const {data} = await api('post', API_UPLOAD_URL, form, {
                    headers: {'Content-Type': 'multipart/form-data'},
                });
                showStatus(uploadText, `File uploaded: ${data.filename}`);
                resultInput.value = `${location.origin}${data.url}`;
            } catch (e) {
                showStatus(uploadText, `Upload failed: ${e.message}`, true);
            }
        };

        uploadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            const file = fileInput.files[0];
            if (file) uploadFile(file);
            fileInput.value = '';
        });

        copyBtn.addEventListener('click', () => {
            if (!resultInput.value) return;
            copyToClipboard(resultInput.value, copyBtn, 'COPY');
        });

        const prevent = (e) => e.preventDefault();
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev =>
            dropArea.addEventListener(ev, prevent, false));

        dropArea.addEventListener('dragenter', () => dropArea.classList.add('dragover'));
        dropArea.addEventListener('dragover', () => dropArea.classList.add('dragover'));
        dropArea.addEventListener('dragleave', () => dropArea.classList.remove('dragover'));
        dropArea.addEventListener('drop', (e) => {
            dropArea.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) uploadFile(file);
        });
    }

    /**
     * Initialize "Images" tab: fetch list and handle deletion.
     */
    function initImagesTab() {
        const imgSection = $(SEL.imgSection);
        const imgTabBtn = $(SEL.imgTabBtn);
        const imgGallery = imgSection?.querySelector(SEL.imageGallery);

        if (!imgSection || !imgGallery || !imgTabBtn) return;

        /**
         * Delete a specific image by filename.
         * @param {string} filename - Name of file to delete.
         * @param {HTMLElement} card - DOM card to remove.
         */
        const deleteImage = async (filename, card) => {
            if (!confirm(`Delete "${filename}"?`)) return;
            try {
                await api('delete', API_DELETE_URL(filename));
                card.remove();

                if (!imgGallery.querySelector('.image-card')) {
                    imgGallery.innerHTML = '<p class="no-images-msg">No images uploaded yet.</p>';
                }
            } catch (e) {
                alert(`Delete failed: ${e.message}`);
            }
        };

        /**
         * Create image card element for gallery
         * @param {string} filename - Image filename
         * @returns {HTMLDivElement} Card element
         */
        const createImageCard = (filename) => {
            const imageUrl = `${location.origin}/images/${filename}`;

            const card = document.createElement('div');
            card.className = 'image-card';
            card.innerHTML = `
                <div class="image-card-preview">
                    <img src="${imageUrl}" alt="${filename}" loading="lazy" />
                </div>
                <div class="image-card-info">
                    <h3 class="image-card-title" title="${filename}">${filename}</h3>
                    <p class="image-card-url" title="${imageUrl}">${imageUrl}</p>
                    <div class="image-card-actions">
                        <button class="copy-url-btn">Copy URL</button>
                        <button class="card-delete-btn" aria-label="Delete image">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
            `;

            card.querySelector('.copy-url-btn').addEventListener('click', () =>
                copyToClipboard(imageUrl, card.querySelector('.copy-url-btn'), 'Copy URL')
            );

            card.querySelector('.card-delete-btn').addEventListener('click', () =>
                deleteImage(filename, card)
            );

            return card;
        };

        /**
         * Load and display the list of uploaded images as cards.
         */
        const loadImages = async () => {
            imgGallery.innerHTML = '';

            try {
                const response = await api('get', API_UPLOAD_URL);
                const files = response.data.items || response.data;

                if (!files || !files.length) {
                    imgGallery.innerHTML = '<p class="no-images-msg">No images uploaded yet.</p>';
                    return;
                }

                const fragment = document.createDocumentFragment();
                files.forEach((file) => {
                    const filename = file.filename || file;
                    const card = createImageCard(filename);
                    fragment.appendChild(card);
                });

                imgGallery.appendChild(fragment);
            } catch (e) {
                imgGallery.innerHTML = `<p class="no-images-msg" style="color: #FF0000">Error loading images: ${e.message}</p>`;
                console.error('Images load error =>', e.message);
            }
        };

        if (imgTabBtn.classList.contains('active')) loadImages();
        imgTabBtn.addEventListener('click', loadImages);
    }

    // Initialize modules
    document.addEventListener('DOMContentLoaded', () => {
        initUploader();
        initImagesTab();
    });
})();
