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


    // 2) Back to Top Button

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
            dietTrack.style.transform = `translateX(-${currentDietIndex * 100}%)`;

            const currentDietKey = dietCards[currentDietIndex].getAttribute("data-diet-key");
            dietFilterButtons.forEach(button => {
                if (button.getAttribute("data-diet") === currentDietKey) {
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
                const selectedDiet = this.getAttribute("data-diet");

                if (selectedDiet === "all") {
                    updateDietCarousel(0);
                    return;
                }

                dietCards.forEach((card, index) => {
                    if (card.getAttribute("data-diet-key") === selectedDiet) {
                        updateDietCarousel(index);
                    }
                });
            });
        });
    }

    const backToTopButton = document.getElementById("backToTopButton");
    if (backToTopButton) {
        // Appear button arrow after roll down 300px
        window.addEventListener("scroll", function () {
            if (window.scrollY > 20 || document.documentElement.scrollTop > 20) {
                backToTopButton.style.display = "block";
            } else {
                backToTopButton.style.display = "none";
            }
        });

        // Smooth when click button
        backToTopButton.addEventListener("click", function () {
            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });
        });
    }

    // 3) Load More Recipes Button
    const loadMoreButton = document.getElementById('load-more-button');
    if (loadMoreButton) {
        const urlParams = new URLSearchParams(window.location.search);

        let currentPage = parseInt(urlParams.get('page')) || 1;

        loadMoreButton.addEventListener('click', function () {
            currentPage++;

            const currentParams = new URLSearchParams(window.location.search);
            currentParams.set('page', currentPage);

            // currentParams
            const newUrl = `${window.location.pathname}?${currentParams.toString()}`;
            window.history.replaceState({ page: currentPage }, '', newUrl);

            loadMoreButton.classList.add('loading');
            loadMoreButton.disabled = true;

            fetch(newUrl)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');

                    // Retrieve the new cards from the fetch operation
                    let allFetchedCards = doc.querySelectorAll('#recipe-container .recipe-card-link');

                    const container = document.getElementById('recipe-container');
                    const currentCardCount = container ? container.querySelectorAll('.recipe-card-link').length : 0;

                    // Extract the new cards
                    const newCards = Array.from(allFetchedCards).slice(currentCardCount);

                    if (newCards.length > 0 && container) {
                        // Insert new cards into container
                        newCards.forEach(card => container.appendChild(card));

                        // Update the displayed figure
                        const totalVisibleCards = container.querySelectorAll('.recipe-card-link').length;
                        const countElement = document.getElementById('displayed-count');
                        if (countElement) {
                            countElement.innerText = totalVisibleCards;
                        }

                        // Check if reached end of recipes
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
    // 4) Save the state before click on card
    document.addEventListener("click", function (e) {
        const cardLink = e.target.closest(".recipe-card-link");
        if (cardLink) {
            // Save the current page scroll position
            sessionStorage.setItem(`${pageKey}_scrollY`, window.scrollY);

            // If a carousel is present (main.html), also save the horizontal scroll position.
            if (track) {
                sessionStorage.setItem(`${pageKey}_trackScrollLeft`, track.scrollLeft);
            }

            // If there is a list of recipes that has been "loaded more" (recipes.html), 
            // save the entire DOM and the number of recipes.
            const container = document.getElementById('recipe-container');
            const countElement = document.getElementById('displayed-count');
            const loadMoreWrapper = document.querySelector('.load-more-wrapper');

            if (container) {
                sessionStorage.setItem(`${pageKey}_containerHTML`, container.innerHTML);
            }
            if (countElement) {
                sessionStorage.setItem(`${pageKey}_countText`, countElement.innerText);
            }
            if (loadMoreWrapper) {
                sessionStorage.setItem(`${pageKey}_loadMoreHTML`, loadMoreWrapper.innerHTML);
            }
        }
    });
});

// 5) RESTORING STATE WHEN CLICKING "GO BACK" and  RETURNING TO THE PAGE 
window.addEventListener("pageshow", function () {
    const pageKey = window.location.pathname;

    // 5a. Restore the list of items loaded via "Load More" and the item count
    const savedContainerHTML = sessionStorage.getItem(`${pageKey}_containerHTML`);
    const savedCountText = sessionStorage.getItem(`${pageKey}_countText`);
    const savedLoadMoreHTML = sessionStorage.getItem(`${pageKey}_loadMoreHTML`);

    const container = document.getElementById('recipe-container');
    const countElement = document.getElementById('displayed-count');
    const loadMoreWrapper = document.querySelector('.load-more-wrapper');

    if (savedContainerHTML && container) {
        container.innerHTML = savedContainerHTML;
        sessionStorage.removeItem(`${pageKey}_containerHTML`);
    }
    if (savedCountText && countElement) {
        countElement.innerText = savedCountText;
        sessionStorage.removeItem(`${pageKey}_countText`);
    }
    if (savedLoadMoreHTML && loadMoreWrapper) {
        loadMoreWrapper.innerHTML = savedLoadMoreHTML;
        sessionStorage.removeItem(`${pageKey}_loadMoreHTML`);
    }

    // 5b. Restore the horizontal scroll position of the carousel (main.html)
    const track = document.querySelector(".carousel-track-container");
    const savedTrackScrollLeft = sessionStorage.getItem(`${pageKey}_trackScrollLeft`);
    if (track && savedTrackScrollLeft !== null) {
        track.scrollLeft = parseInt(savedTrackScrollLeft, 10);
        sessionStorage.removeItem(`${pageKey}_trackScrollLeft`);
    }

    // 5c. Restore vertical page scroll position
    const savedScrollY = sessionStorage.getItem(`${pageKey}_scrollY`);
    if (savedScrollY !== null) {
        setTimeout(function () {
            window.scrollTo({
                top: parseInt(savedScrollY, 10),
                behavior: "instant"
            });
            sessionStorage.removeItem(`${pageKey}_scrollY`);
        }, 50);
    }
});