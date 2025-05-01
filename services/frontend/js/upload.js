/**
 * Image-host front-end logic
 * - Upload via button or drag-&-drop
 * - List uploaded images
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
        tableHeader: '.table-header',
        imgTabBtn: '.tab[data-tab="images"]',
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
     * Create a paragraph DOM element to show status/info.
     * @param {string} txt - Text to display.
     * @param {string} [col='#555'] - Text color.
     * @returns {HTMLParagraphElement}
     */
    const createMsg = (txt, col = '#555') => {
        const p = document.createElement('p');
        p.textContent = txt;
        p.className = 'no-images-msg';
        p.style.cssText = `text-align:center;color:${col}`;
        return p;
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
            return await axios({ method, url, data, ...cfg });
        } catch (e) {
            throw {
                status: e.response?.status ?? null,
                message: e.response?.data?.detail || e.message || 'Unknown error',
            };
        }
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
                const { data } = await api('post', API_UPLOAD_URL, form, {
                    headers: { 'Content-Type': 'multipart/form-data' },
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

        copyBtn.addEventListener('click', async () => {
            if (!resultInput.value) return;
            await navigator.clipboard.writeText(resultInput.value);
            copyBtn.textContent = 'Copied!';
            setTimeout(() => (copyBtn.textContent = 'COPY'), 1500);
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
        const tableHeader = $(SEL.tableHeader);
        const imgTabBtn = $(SEL.imgTabBtn);
        if (!imgSection || !tableHeader || !imgTabBtn) return;

        /**
         * Delete a specific image by filename.
         * @param {string} filename - Name of file to delete.
         * @param {HTMLElement} row - DOM row to remove.
         */
        const deleteImage = async (filename, row) => {
            if (!confirm(`Delete "${filename}"?`)) return;
            try {
                await api('delete', API_DELETE_URL(filename));
                row.remove();
                if (!imgSection.querySelector('.table-row')) {
                    tableHeader.style.display = 'none';
                    imgSection.appendChild(createMsg('No images yet.'));
                }
            } catch (e) {
                alert(`Delete failed: ${e.message}`);
            }
        };

        /**
         * Load and display the list of uploaded images.
         */
        const loadImages = async () => {
            imgSection.querySelectorAll('.table-row, .no-images-msg').forEach(n => n.remove());

            try {
                const { data: files } = await api('get', API_UPLOAD_URL);

                if (!files.length) {
                    tableHeader.style.display = 'none';
                    imgSection.appendChild(createMsg('No images yet.'));
                    return;
                }
                tableHeader.style.display = 'flex';

                files.forEach(({ filename }) => {
                    const row = document.createElement('div');
                    row.className = 'table-row';
                    row.innerHTML = `
                        <div class="file-name">
                          <img src="${location.origin}/images/${filename}" alt="" class="file-icon" />
                          <span>${filename}</span>
                        </div>
                        <div class="file-url">${location.origin}/images/${filename}</div>
                        <div class="file-delete">
                          <button class="delete-btn"><i class="fas fa-trash-alt"></i></button>
                        </div>`;
                    row.querySelector('.delete-btn')
                        .addEventListener('click', () => deleteImage(filename, row));
                    imgSection.appendChild(row);
                });
            } catch (e) {
                tableHeader.style.display = 'none';
                if (e.status === 404) {
                    imgSection.appendChild(createMsg('No images yet.'));
                } else {
                    imgSection.appendChild(createMsg(`Error: ${e.message}`, '#FF0000'));
                    console.error('Images load error ⇒', e.message);
                }
            }
        };

        if (imgTabBtn.classList.contains('active')) loadImages();
        imgTabBtn.addEventListener('click', loadImages);
    }

    // Initialize modules
    initUploader();
    initImagesTab();
})();
