// GhibliAI Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const uploadZone = document.getElementById('upload-zone');
    const processingZone = document.getElementById('processing-zone');
    const resultZone = document.getElementById('result-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const fileTypeLabel = document.getElementById('file-type-label');
    const processingMessage = document.getElementById('processing-message');
    const originalContainer = document.getElementById('original-container');
    const resultContainer = document.getElementById('result-container');
    const downloadBtn = document.getElementById('download-btn');
    const newUploadBtn = document.getElementById('new-upload-btn');
    const strengthSlider = document.getElementById('strength-slider');
    const strengthValue = document.getElementById('strength-value');
    const qualitySelect = document.getElementById('quality-select');
    const processingTime = document.getElementById('processing-time');
    const shareButtons = document.querySelectorAll('.share-btn');

    // Current task ID
    let currentTaskId = null;
    let statusCheckInterval = null;
    let originalFile = null;
    let isVideo = false;

    // Initialize drag and drop
    initDragAndDrop();

    // Initialize button handlers
    browseBtn.addEventListener('click', function() {
        fileInput.click();
    });

    fileInput.addEventListener('change', function(e) {
        if (fileInput.files.length > 0) {
            handleFileUpload(fileInput.files[0]);
        }
    });

    newUploadBtn.addEventListener('click', function() {
        resetUI();
    });

    // Transformation strength slider
    strengthSlider.addEventListener('input', function() {
        strengthValue.textContent = `${strengthSlider.value}%`;
    });

    // Share buttons
    shareButtons.forEach(button => {
        button.addEventListener('click', function() {
            const platform = this.getAttribute('data-platform');
            shareResult(platform);
        });
    });

    // Drag and drop functionality
    function initDragAndDrop() {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, unhighlight, false);
        });

        uploadZone.addEventListener('drop', handleDrop, false);
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        uploadZone.classList.add('dragover');
    }

    function unhighlight() {
        uploadZone.classList.remove('dragover');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    }

    // File upload handling
    function handleFileUpload(file) {
        // Check file type
        const fileType = file.type;
        if (!fileType.startsWith('image/') && !fileType.startsWith('video/')) {
            alert('Please upload an image or video file.');
            return;
        }

        // Check file size (max 100MB)
        if (file.size > 100 * 1024 * 1024) {
            alert('File size exceeds 100MB limit.');
            return;
        }

        // Save original file for preview
        originalFile = file;
        isVideo = fileType.startsWith('video/');

        // Update UI based on file type
        fileTypeLabel.textContent = isVideo ? 'Video' : 'Image';
        
        if (isVideo) {
            processingMessage.textContent = 'Video processing may take several minutes depending on length and resolution';
        } else {
            processingMessage.textContent = 'Image processing typically takes 30-60 seconds';
        }

        // Show processing UI
        uploadZone.classList.add('d-none');
        processingZone.classList.remove('d-none');
        resultZone.classList.add('d-none');

        // Reset progress
        updateProgress(0);

        // Get transformation settings
        const strength = strengthSlider.value / 100; // Convert percentage to decimal
        let steps = 20; // Default balanced setting
        
        switch (qualitySelect.value) {
            case 'fast':
                steps = 15;
                break;
            case 'balanced':
                steps = 20;
                break;
            case 'quality':
                steps = 30;
                break;
        }

        // Upload file
        const formData = new FormData();
        formData.append('file', file);
        formData.append('strength', strength);
        formData.append('steps', steps);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                return;
            }

            currentTaskId = data.task_id;
            startStatusCheck();
        })
        .catch(error => {
            showError('Upload failed: ' + error.message);
        });
    }

    // Status checking
    function startStatusCheck() {
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
        }

        statusCheckInterval = setInterval(checkStatus, 1000);
    }

    function checkStatus() {
        if (!currentTaskId) return;

        fetch(`/status/${currentTaskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                    clearInterval(statusCheckInterval);
                    return;
                }

                updateProgress(data.progress);

                if (data.status === 'completed') {
                    clearInterval(statusCheckInterval);
                    showResult(data);
                } else if (data.status === 'failed') {
                    showError(data.error || 'Processing failed');
                    clearInterval(statusCheckInterval);
                }
            })
            .catch(error => {
                showError('Status check failed: ' + error.message);
                clearInterval(statusCheckInterval);
            });
    }

    // UI updates
    function updateProgress(progress) {
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${progress}%`;
    }

    function showResult(data) {
        // Show result UI
        uploadZone.classList.add('d-none');
        processingZone.classList.add('d-none');
        resultZone.classList.remove('d-none');

        // Display original file
        displayMedia(originalContainer, originalFile);

        // Display result
        const resultUrl = data.result_url;
        
        // Determine if it's a video or image based on is_video flag
        if (data.is_video) {
            const video = document.createElement('video');
            video.controls = true;
            video.autoplay = false;
            video.src = resultUrl;
            resultContainer.innerHTML = '';
            resultContainer.appendChild(video);
        } else {
            const img = document.createElement('img');
            img.src = resultUrl;
            resultContainer.innerHTML = '';
            resultContainer.appendChild(img);
        }

        // Set download link
        downloadBtn.href = resultUrl;
        downloadBtn.download = `ghibli_${data.original_filename}`;
        
        // Show processing time if available
        if (data.processing_time) {
            const seconds = Math.round(data.processing_time);
            processingTime.querySelector('span').textContent = seconds;
            processingTime.classList.remove('d-none');
        } else {
            processingTime.classList.add('d-none');
        }
    }

    function displayMedia(container, file) {
        container.innerHTML = '';
        
        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            container.appendChild(img);
        } else if (file.type.startsWith('video/')) {
            const video = document.createElement('video');
            video.controls = true;
            video.autoplay = false;
            video.src = URL.createObjectURL(file);
            container.appendChild(video);
        }
    }

    function showError(message) {
        alert('Error: ' + message);
        resetUI();
    }

    function resetUI() {
        // Reset file input
        fileInput.value = '';
        originalFile = null;
        isVideo = false;

        // Show upload UI
        uploadZone.classList.remove('d-none');
        processingZone.classList.add('d-none');
        resultZone.classList.add('d-none');

        // Clear intervals
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            statusCheckInterval = null;
        }

        // Reset task ID
        currentTaskId = null;
    }
    
    function shareResult(platform) {
        // Get the result URL
        const resultUrl = downloadBtn.href;
        let shareUrl = '';
        
        switch(platform) {
            case 'facebook':
                shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}`;
                break;
            case 'twitter':
                shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent('Check out my Studio Ghibli style image created with GhibliAI!')}&url=${encodeURIComponent(window.location.href)}`;
                break;
            case 'pinterest':
                shareUrl = `https://pinterest.com/pin/create/button/?url=${encodeURIComponent(window.location.href)}&media=${encodeURIComponent(resultUrl)}&description=${encodeURIComponent('My Studio Ghibli style image created with GhibliAI')}`;
                break;
        }
        
        if (shareUrl) {
            window.open(shareUrl, '_blank', 'width=600,height=400');
        }
    }
});
