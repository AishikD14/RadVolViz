window.dash_clientside = window.dash_clientside || {};

window.dash_clientside.clientside = {
    changeStyle: function(value) {
        let parentElement = document.querySelector(value);

        const firstChild = parentElement.querySelector('.js-plotly-plot');

        // Remove the visibility style
        firstChild.style.removeProperty('visibility');
    }
};

const observer = new MutationObserver((mutations, obs) => {
    const elements = document.getElementsByClassName('js-plotly-plot'); // No dot needed
    if (elements.length > 0) {

        for (let i = 0; i < elements.length; i++) {
            elements[i].style.visibility = 'hidden';
        }

        obs.disconnect(); // Stop observing once elements are found and modified
    }
});

// Observe changes in the entire document
observer.observe(document.body, { childList: true, subtree: true });
