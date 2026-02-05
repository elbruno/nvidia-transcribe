// JavaScript interop functions for Blazor components

/**
 * Clicks an HTML element programmatically
 * @param {HTMLElement} element - The element to click
 */
function clickElement(element) {
    if (element) {
        element.click();
    }
}

/**
 * Copies text to the clipboard
 * @param {string} text - The text to copy
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        return true;
    }
}

/**
 * Downloads text content as a file
 * @param {string} content - The file content
 * @param {string} fileName - The file name
 */
function downloadTextFile(content, fileName) {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Scrolls an element to the bottom
 * @param {HTMLElement} element - The element to scroll
 */
function scrollToBottom(element) {
    if (element) {
        element.scrollTop = element.scrollHeight;
    }
}
