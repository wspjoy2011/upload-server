/**
 * Image-host front-end logic
 * - Upload via button or drag-&-drop
 * - List uploaded images as cards with pagination
 * - Delete images
 */
(() => {
    /* --------------------------------------------------------------------
     *  CONSTANTS
     * ------------------------------------------------------------------ */
    const API_UPLOAD_URL = `${location.origin}/api/upload/`;
    const API_DELETE_URL = (fn) => `${location.origin}/api/upload/${encodeURIComponent(fn)}`;

    const LS_KEYS = {
        PER_PAGE: 'image_host_per_page',
        ACTIVE_TAB: 'image_host_active_tab',
        SORT_ORDER: 'image_host_sort_order'
    };

    const DEFAULT_PAGE = 1;
    const DEFAULT_PER_PAGE = 8;
    const AVAILABLE_PER_PAGE = [4, 8, 12];
    const DEFAULT_TAB = 'upload';
    const DEFAULT_SORT_ORDER = 'desc';
    const VALID_TABS = ['upload', 'images'];
    const VALID_SORT_ORDERS = ['desc', 'asc'];

    const SEL = {
        uploadBtn: '#uploadBtn',
        fileInput: '#fileInput',
        resultInput: '#resultLink',
        copyBtn: '#copyBtn',
        uploadText: '.upload-main-text, .upload-error',
        dropArea: '#dropArea',
        imgSection: '#images-tab',
        uploadSection: '#upload-tab',
        imgTabBtn: '.tab[data-tab="images"]',
        uploadTabBtn: '.tab[data-tab="upload"]',
        allTabs: '.tab',
        allTabContent: '.tab-content',
        imageGallery: '.image-gallery',
        prevPageBtn: '#prevPage',
        nextPageBtn: '#nextPage',
        currentPageSpan: '#currentPage',
        totalPagesSpan: '#totalPages',
        perPageSelect: '#perPageSelect',
        sortSelect: '#sortSelect'
    };

    const $ = (s) => document.querySelector(s);
    const $$ = (s) => document.querySelectorAll(s);

    let loadImagesFunction = null;

    const getSavedPerPage = () => {
        const saved = localStorage.getItem(LS_KEYS.PER_PAGE);
        if (saved && AVAILABLE_PER_PAGE.includes(parseInt(saved))) {
            return parseInt(saved);
        }
        return DEFAULT_PER_PAGE;
    };

    const savePerPage = (perPage) => {
        localStorage.setItem(LS_KEYS.PER_PAGE, perPage.toString());
    };

    const getSavedActiveTab = () => {
        const savedTab = localStorage.getItem(LS_KEYS.ACTIVE_TAB);
        return savedTab || DEFAULT_TAB;
    };

    const saveActiveTab = (tab) => {
        localStorage.setItem(LS_KEYS.ACTIVE_TAB, tab);
    };

    const getSavedSortOrder = () => {
        const saved = localStorage.getItem(LS_KEYS.SORT_ORDER);
        if (saved && VALID_SORT_ORDERS.includes(saved)) {
            return saved;
        }
        return DEFAULT_SORT_ORDER;
    };

    const saveSortOrder = (sortOrder) => {
        localStorage.setItem(LS_KEYS.SORT_ORDER, sortOrder);
    };

    /**
     * Get URL search parameter value
     * @param {string} paramName - Parameter name to get
     * @returns {string|null} Parameter value or null if not found
     */
    const getUrlParam = (paramName) => {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(paramName);
    };

    /**
     * Update URL parameter without page reload
     * @param {string} paramName - Parameter name
     * @param {string} value - Parameter value
     */
    const updateUrlParam = (paramName, value) => {
        const url = new URL(window.location);
        url.searchParams.set(paramName, value);
        window.history.replaceState({}, '', url);
    };

    /**
     * Remove URL parameter without page reload
     * @param {string} paramName - Parameter name to remove
     */
    const removeUrlParam = (paramName) => {
        const url = new URL(window.location);
        url.searchParams.delete(paramName);
        window.history.replaceState({}, '', url);
    };

    /**
     * Update pagination-related URL parameters
     * @param {number} page - Current page
     * @param {number} perPage - Items per page
     * @param {string} order - Sort order
     */
    const updatePaginationUrlParams = (page, perPage, order) => {
        const url = new URL(window.location);
        url.searchParams.set('page', page.toString());
        url.searchParams.set('per_page', perPage.toString());
        url.searchParams.set('order', order);
        window.history.replaceState({}, '', url);
    };

    /**
     * Remove pagination-related URL parameters
     */
    const removePaginationUrlParams = () => {
        const url = new URL(window.location);
        url.searchParams.delete('page');
        url.searchParams.delete('per_page');
        url.searchParams.delete('order');
        window.history.replaceState({}, '', url);
    };

    /**
     * Initialize pagination state from URL parameters
     */
    const initPaginationFromUrl = () => {
        const urlPage = getUrlParam('page');
        const urlPerPage = getUrlParam('per_page');
        const urlOrder = getUrlParam('order');

        if (urlPage) {
            const pageNum = parseInt(urlPage);
            if (pageNum > 0) {
                paginationState.currentPage = pageNum;
            }
        }

        if (urlPerPage) {
            const perPageNum = parseInt(urlPerPage);
            if (AVAILABLE_PER_PAGE.includes(perPageNum)) {
                paginationState.perPage = perPageNum;
            }
        }

        if (urlOrder && VALID_SORT_ORDERS.includes(urlOrder)) {
            paginationState.sortOrder = urlOrder;
        }
    };

    /**
     * Determine which tab should be active based on URL param, localStorage, or default
     * @returns {string} Tab ID to activate
     */
    const getTabToActivate = () => {
        const urlTab = getUrlParam('tab');
        if (urlTab && VALID_TABS.includes(urlTab)) {
            return urlTab;
        }

        const savedTab = getSavedActiveTab();
        if (VALID_TABS.includes(savedTab)) {
            return savedTab;
        }

        return DEFAULT_TAB;
    };

    const paginationState = {
        currentPage: DEFAULT_PAGE,
        perPage: getSavedPerPage(),
        totalPages: 1,
        totalItems: 0,
        sortOrder: getSavedSortOrder()
    };

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

            if (method.toLowerCase() === 'get' && url.startsWith(API_UPLOAD_URL) && error.status === 404) {
                return {data: {items: [], pagination: {total: 0, pages: 0}}};
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
     * Initialize tabs functionality with localStorage and URL parameter support
     */
    function initTabs() {
        const tabs = $$(SEL.allTabs);
        const tabContents = $$(SEL.allTabContent);

        if (!tabs.length || !tabContents.length) return;

        const activateTab = (tabId, updateUrl = true) => {
            tabContents.forEach(content => content.classList.add('hidden'));
            tabs.forEach(tab => {
                tab.classList.remove('active');
                tab.classList.add('inactive');
            });

            const targetContent = $(`#${tabId}-tab`);
            const targetTab = $(`.tab[data-tab="${tabId}"]`);

            if (targetContent) targetContent.classList.remove('hidden');
            if (targetTab) {
                targetTab.classList.add('active');
                targetTab.classList.remove('inactive');
            }

            if (updateUrl) {
                updateUrlParam('tab', tabId);

                if (tabId === 'images') {
                    initPaginationFromUrl();
                    updatePaginationUrlParams(
                        paginationState.currentPage,
                        paginationState.perPage,
                        paginationState.sortOrder
                    );
                } else {
                    removePaginationUrlParams();
                }
            }

            saveActiveTab(tabId);

            if (tabId === 'images' && loadImagesFunction) {
                loadImagesFunction();
            }
        };

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabId = tab.getAttribute('data-tab');
                if (tabId && VALID_TABS.includes(tabId)) {
                    activateTab(tabId, true);
                }
            });
        });

        window.activateTabOnLoad = () => {
            const tabToActivate = getTabToActivate();

            if (tabToActivate === 'images') {
                initPaginationFromUrl();
            }

            activateTab(tabToActivate, !getUrlParam('tab'));
        };
    }

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
        const prevPageBtn = $(SEL.prevPageBtn);
        const nextPageBtn = $(SEL.nextPageBtn);
        const currentPageSpan = $(SEL.currentPageSpan);
        const totalPagesSpan = $(SEL.totalPagesSpan);
        const perPageSelect = $(SEL.perPageSelect);
        const sortSelect = $(SEL.sortSelect);

        if (!imgSection || !imgGallery || !imgTabBtn || !perPageSelect || !sortSelect) return;

        /**
         * Update UI selects with current pagination state
         */
        const updateSelectsFromState = () => {
            perPageSelect.value = paginationState.perPage.toString();
            sortSelect.value = paginationState.sortOrder;
        };

        /**
         * Update pagination UI elements
         */
        const updatePaginationUI = () => {
            currentPageSpan.textContent = paginationState.currentPage;
            totalPagesSpan.textContent = paginationState.totalPages || 1;

            prevPageBtn.disabled = paginationState.currentPage <= 1;
            nextPageBtn.disabled = paginationState.currentPage >= paginationState.totalPages;

            // Update URL parameters
            updatePaginationUrlParams(
                paginationState.currentPage,
                paginationState.perPage,
                paginationState.sortOrder
            );
        };

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

                paginationState.totalItems--;
                paginationState.totalPages = Math.max(
                    1,
                    Math.ceil(paginationState.totalItems / paginationState.perPage)
                );

                if (!imgGallery.querySelector('.image-card') && paginationState.currentPage > 1) {
                    paginationState.currentPage--;
                    loadImages();
                } else if (!imgGallery.querySelector('.image-card')) {
                    imgGallery.innerHTML = '<p class="no-images-msg">No images uploaded yet.</p>';
                    updatePaginationUI();
                } else {
                    updatePaginationUI();
                }
            } catch (e) {
                alert(`Delete failed: ${e.message}`);
            }
        };

        /**
         * Create image card element for gallery
         * @param {object} image - Image object with filename and other properties
         * @returns {HTMLDivElement} Card element
         */
        const createImageCard = (image) => {
            const filename = image.filename;
            const imageUrl = `${location.origin}${image.url || '/images/' + filename}`;

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
         * Load and display the list of uploaded images as cards with pagination.
         */
        const loadImages = async () => {
            imgGallery.innerHTML = '<div class="loading-spinner-container"><div class="loading-spinner"><i class="fas fa-spinner fa-pulse fa-4x"></i></div></div>';

            const paginationControls = $('.pagination-controls');
            if (paginationControls) {
                paginationControls.classList.add('hidden');
            }

            updateSelectsFromState();

            try {
                const url = `${API_UPLOAD_URL}?page=${paginationState.currentPage}&per_page=${paginationState.perPage}&order=${paginationState.sortOrder}`;
                const response = await api('get', url);
                const data = response.data;

                const files = data.items || data;
                const pagination = data.pagination || {};

                imgGallery.innerHTML = '';

                paginationState.totalItems = pagination.total || files.length;
                paginationState.totalPages = pagination.pages || Math.ceil(files.length / paginationState.perPage) || 1;

                if (!files || !files.length) {
                    imgGallery.innerHTML = '<p class="no-images-msg">No images uploaded yet.</p>';
                    updatePaginationUI();

                    if (paginationControls) {
                        paginationControls.classList.remove('hidden');
                    }

                    return;
                }

                const fragment = document.createDocumentFragment();
                files.forEach((file) => {
                    const fileObj = typeof file === 'string' ? {filename: file} : file;
                    const card = createImageCard(fileObj);
                    fragment.appendChild(card);
                });

                imgGallery.appendChild(fragment);
                updatePaginationUI();

                if (paginationControls) {
                    paginationControls.classList.remove('hidden');
                }

            } catch (e) {
                imgGallery.innerHTML = `<p class="no-images-msg" style="color: #FF0000">Error loading images: ${e.message}</p>`;
                console.error('Images load error =>', e.message);
            }
        };

        // Event listeners
        perPageSelect.addEventListener('change', () => {
            const newPerPage = parseInt(perPageSelect.value);
            if (AVAILABLE_PER_PAGE.includes(newPerPage) && newPerPage !== paginationState.perPage) {
                paginationState.perPage = newPerPage;
                paginationState.currentPage = 1;
                savePerPage(newPerPage);
                loadImages();
            }
        });

        sortSelect.addEventListener('change', () => {
            const newSortOrder = sortSelect.value;
            if (VALID_SORT_ORDERS.includes(newSortOrder) && newSortOrder !== paginationState.sortOrder) {
                paginationState.sortOrder = newSortOrder;
                paginationState.currentPage = 1;
                saveSortOrder(newSortOrder);
                loadImages();
            }
        });

        prevPageBtn.addEventListener('click', () => {
            if (paginationState.currentPage > 1) {
                paginationState.currentPage--;
                loadImages();
            }
        });

        nextPageBtn.addEventListener('click', () => {
            if (paginationState.currentPage < paginationState.totalPages) {
                paginationState.currentPage++;
                loadImages();
            }
        });

        loadImagesFunction = loadImages;
    }

    // Initialize modules
    document.addEventListener('DOMContentLoaded', () => {
        initTabs();
        initUploader();
        initImagesTab();

        if (window.activateTabOnLoad) {
            window.activateTabOnLoad();
        }
    });
})();
