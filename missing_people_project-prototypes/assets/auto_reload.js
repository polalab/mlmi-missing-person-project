// This script auto-reloads the page after 5 minutes of no interaction

(function() {
    let timer;

    function resetTimer() {
        clearTimeout(timer);
        timer = setTimeout(() => {
            location.reload(); // Reload the page
        }, 5 * 60 * 1000); // 5 minutes
    }

    window.onload = resetTimer;
    document.onmousemove = resetTimer;
    document.onkeypress = resetTimer;
    document.ontouchstart = resetTimer;
    document.onclick = resetTimer;
})();
