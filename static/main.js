function goBackToPreviousPage() {
    // If have a previous page, and it isn't the recipes pages 
    if (document.referrer && !document.referrer.includes(window.location.pathname)) {
        window.location.href = document.referrer;
    } else {
        window.location.href = "/";
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const pageKey = window.location.pathname;

    // 1) Get the carousel track and buttons
    const track = document.querySelector(".carousel-track-container");
    const prevButton = document.getElementById("prevButton");
    const nextButton = document.getElementById("nextButton");

    if (track && prevButton && nextButton) {
        // Check function and disappear button when reach the end of the carousel
        function updateArrows() {
            const scrollLeft = track.scrollLeft;
            const maxScrollLeft = track.scrollWidth - track.clientWidth;

            // if in the left end of the carousel, hide the left arrow
            if (scrollLeft <= 5) {
                prevButton.style.display = "none";
            } else {
                prevButton.style.display = "flex";
            }

            // if in the right end of the carousel, hide the right arrow
            if (scrollLeft >= maxScrollLeft - 5) {
                nextButton.style.display = "none";
            } else {
                nextButton.style.display = "flex";
            }
        }
        // To update the arrows when the page loads, 
        // if the carousel is already scrolled to the end (left or right)
        track.addEventListener("scroll", updateArrows);

        // go to the right
        nextButton.addEventListener("click", function () {
            const firstCard = track.querySelector(".recipe-card");
            if (firstCard) {
                const cardWidth = firstCard.offsetWidth + 24; // width of 1 card + gap
                track.scrollBy({ left: cardWidth, behavior: "smooth" });
                setTimeout(updateArrows, 300);
            }
        });

        // go to the left
        prevButton.addEventListener("click", function () {
            const firstCard = track.querySelector(".recipe-card");
            if (firstCard) {
                const cardWidth = firstCard.offsetWidth + 24;
                track.scrollBy({ left: -cardWidth, behavior: "smooth" });
                setTimeout(updateArrows, 300);
            }
        });

        // Update the arrows when the page loads
        updateArrows();
    }
    // 2) Diet Carousel
    const dietTrack = document.querySelector(".diet-carousel-track");
    const dietCards = document.querySelectorAll(".diet-card-item");
    const dietPrevButton = document.getElementById("dietPrevButton");
    const dietNextButton = document.getElementById("dietNextButton");
    const dietFilterButtons = document.querySelectorAll(".profile-setup-section .diet-chip");

    if (dietTrack && dietCards.length > 0) {
        let currentDietIndex = 0;
        const totalDietCards = dietCards.length;

        function updateDietCarousel(index) {
            if (index < 0) index = 0;
            if (index >= totalDietCards) index = totalDietCards - 1;

            currentDietIndex = index;
            dietTrack.style.transform = 'translateX(-' + (currentDietIndex * 100) + '%)';

            // Active Filter button to connect with the current diet card
            const currentDietKey = (dietCards[currentDietIndex].getAttribute("data-diet-key") || "").toLowerCase().trim();
            dietFilterButtons.forEach(button => {
                const buttonDiet = (button.getAttribute("data-diet") || "").toLowerCase().trim();
                if (buttonDiet === currentDietKey) {
                    button.classList.add("active");
                } else {
                    button.classList.remove("active");
                }
            });
        }

        if (dietNextButton) {
            dietNextButton.addEventListener("click", function () {
                if (currentDietIndex < totalDietCards - 1) {
                    updateDietCarousel(currentDietIndex + 1);
                } else {
                    updateDietCarousel(0);
                }
            });
        }

        if (dietPrevButton) {
            dietPrevButton.addEventListener("click", function () {
                if (currentDietIndex > 0) {
                    updateDietCarousel(currentDietIndex - 1);
                } else {
                    updateDietCarousel(totalDietCards - 1);
                }
            });
        }

        dietFilterButtons.forEach(button => {
            button.addEventListener("click", function () {
                const selectedDiet = (this.getAttribute("data-diet") || "").toLowerCase().trim();

                if (selectedDiet === "all") {
                    updateDietCarousel(0);
                    return;
                }

                dietCards.forEach((card, index) => {
                    const cardKey = (card.getAttribute("data-diet-key") || "").toLowerCase().trim();
                    if (cardKey === selectedDiet) {
                        updateDietCarousel(index);
                    }
                });
            });
        });
    }
    // 3) Back to Top Button
    const backToTopButton = document.getElementById("backToTopButton");
    if (backToTopButton) {
        window.addEventListener("scroll", function () {
            if (window.scrollY > 20 || document.documentElement.scrollTop > 20) {
                backToTopButton.style.display = "block";
            } else {
                backToTopButton.style.display = "none";
            }
        });

        backToTopButton.addEventListener("click", function () {
            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });
        });
    }

    // 4) Load More Recipes Button
    const loadMoreButton = document.getElementById('load-more-button');
    if (loadMoreButton) {
        const urlParams = new URLSearchParams(window.location.search);
        let currentPage = parseInt(urlParams.get('page')) || 1;

        loadMoreButton.addEventListener('click', function () {
            currentPage++;

            const currentParams = new URLSearchParams(window.location.search);
            currentParams.set('page', currentPage);

            const url = new URL(window.location.href);
            url.search = currentParams.toString();
            const newUrl = url.pathname + url.search;
            window.history.replaceState({ page: currentPage }, '', newUrl);

            loadMoreButton.classList.add('loading');
            loadMoreButton.disabled = true;

            fetch(newUrl)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');

                    let allFetchedCards = doc.querySelectorAll('#recipe-container .recipe-card-link');
                    const container = document.getElementById('recipe-container');
                    const currentCardCount = container ? container.querySelectorAll('.recipe-card-link').length : 0;

                    const newCards = Array.from(allFetchedCards).slice(currentCardCount);

                    if (newCards.length > 0 && container) {
                        newCards.forEach(card => container.appendChild(card));

                        const totalVisibleCards = container.querySelectorAll('.recipe-card-link').length;
                        const countElement = document.getElementById('displayed-count');
                        if (countElement) {
                            countElement.innerText = totalVisibleCards;
                        }

                        if (allFetchedCards.length < currentPage * 15) {
                            loadMoreButton.parentElement.innerHTML = '<div class="reached-end-badge"><span class="end-icon">✨</span><span>You\'ve reached the end of the list!</span></div>';
                        } else {
                            loadMoreButton.classList.remove('loading');
                            loadMoreButton.disabled = false;
                        }
                    } else {
                        loadMoreButton.parentElement.innerHTML = '<div class="reached-end-badge"><span class="end-icon">✨</span><span>You\'ve reached the end of the list!</span></div>';
                    }
                })
                .catch(err => {
                    console.error("Error loading more recipes:", err);
                    loadMoreButton.classList.remove('loading');
                    loadMoreButton.disabled = false;
                });
        });
    }
    // 5) Save the state before click on card
    document.addEventListener("click", function (e) {
        const Link = e.target.closest("a, .recipe-card-link, .button-primary");
        if (Link) {
            sessionStorage.setItem(pageKey + '_scrollY', window.scrollY);

            const currentTrack = document.querySelector(".carousel-track-container");
            if (currentTrack) {
                sessionStorage.setItem(pageKey + '_trackScrollLeft', currentTrack.scrollLeft);
            }

            const container = document.getElementById('recipe-container');
            const countElement = document.getElementById('displayed-count');
            const loadMoreWrapper = document.querySelector('.load-more-wrapper');

            if (container) {
                sessionStorage.setItem(pageKey + '_containerHTML', container.innerHTML);
            }
            if (countElement) {
                sessionStorage.setItem(pageKey + '_countText', countElement.innerText);
            }
            if (loadMoreWrapper) {
                sessionStorage.setItem(pageKey + '_loadMoreHTML', loadMoreWrapper.innerHTML);
            }
        }
    });
});

// 6) Restore State when clicking "GO BACK" and  Return to the previous page (recipes.html or main.html) 
window.addEventListener("pageshow", function () {
    const pageKey = window.location.pathname;

    // 6a. Restore the list of items loaded via "Load More" and the item count
    const savedContainerHTML = sessionStorage.getItem(pageKey + '_containerHTML');
    const savedCountText = sessionStorage.getItem(pageKey + '_countText');
    const savedLoadMoreHTML = sessionStorage.getItem(pageKey + '_loadMoreHTML');

    const container = document.getElementById('recipe-container');
    const countElement = document.getElementById('displayed-count');
    const loadMoreWrapper = document.querySelector('.load-more-wrapper');

    if (savedContainerHTML && container) {
        container.innerHTML = savedContainerHTML;
        sessionStorage.removeItem(pageKey + '_containerHTML');
    }
    if (savedCountText && countElement) {
        countElement.innerText = savedCountText;
        sessionStorage.removeItem(pageKey + '_countText');
    }
    if (savedLoadMoreHTML && loadMoreWrapper) {
        loadMoreWrapper.innerHTML = savedLoadMoreHTML;
        sessionStorage.removeItem(pageKey + '_loadMoreHTML');
    }

    // 6b. Restore the horizontal scroll position of the carousel (main.html)
    const track = document.querySelector(".carousel-track-container");
    const savedTrackScrollLeft = sessionStorage.getItem(pageKey + '_trackScrollLeft');
    if (track && savedTrackScrollLeft !== null) {
        track.scrollLeft = parseInt(savedTrackScrollLeft, 10);
        sessionStorage.removeItem(pageKey + '_trackScrollLeft');
    }

    // 6c. Restore vertical page scroll position
    if ('scrollRestoration' in history) {
        history.scrollRestoration = 'manual'; // Avoid the browser's default scroll restoration behavior
    }

    const savedScrollY = sessionStorage.getItem(pageKey + '_scrollY');
    if (savedScrollY !== null) {
        setTimeout(function () {
            window.scrollTo(0, parseInt(savedScrollY, 10));
            sessionStorage.removeItem(pageKey + '_scrollY');
        }, 120);
    }
});