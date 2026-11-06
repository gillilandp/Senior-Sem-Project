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

        // Enable Drag / Swipe Scroll without needing arrow buttons
        let isDown = false;
        let startX;
        let scrollLeftPos;
        let isDragging = false;

        track.addEventListener('mousedown', (e) => {
            isDown = true;
            isDragging = false;
            track.classList.add('active');
            startX = e.pageX - track.offsetLeft;
            scrollLeftPos = track.scrollLeft;
        });

        track.addEventListener('mouseleave', () => {
            isDown = false;
            track.classList.remove('active');
        });

        track.addEventListener('mouseup', () => {
            isDown = false;
            track.classList.remove('active');
        });

        track.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            const x = e.pageX - track.offsetLeft;
            const walk = (x - startX) * 2;
            if (Math.abs(walk) > 5) {
                isDragging = true;
                e.preventDefault();
                track.scrollLeft = scrollLeftPos - walk;
            }
        });

        track.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', (e) => {
                if (isDragging) {
                    e.preventDefault();
                }
            });
        });
    }

    // 2) Coverflow 3D Diet Carousel
    const coverflowCards = document.querySelectorAll(".coverflow-card");
    const dietPrevButton = document.getElementById("dietPrevButton");
    const dietNextButton = document.getElementById("dietNextButton");
    const dietFilterButtons = document.querySelectorAll(".profile-setup-section .diet-chip, .filter-tags .diet-chip");

    if (coverflowCards.length > 0) {
        let currentIndex = 0;
        const totalCards = coverflowCards.length;

        function normalizeKey(str) {
            return (str || "").toLowerCase().replace(/_/g, "-").trim();
        }

        function updateCoverflow(index) {

            currentIndex = (index + totalCards) % totalCards; // Wrap around

            coverflowCards.forEach((card, i) => {
                card.className = "coverflow-card"; // Reset old class
                let diff = i - currentIndex;

                if (diff < -Math.floor(totalCards / 2)) diff += totalCards;
                if (diff > Math.floor(totalCards / 2)) diff -= totalCards;

                if (diff === 0) {
                    card.classList.add("active");
                } else if (diff === -1) {
                    card.classList.add("prev-1");
                } else if (diff === 1) {
                    card.classList.add("next-1");
                } else {
                    card.classList.add("hidden");
                }
            });

            // Synchronize the Active effect for the Diet Chip button
            const currentDietKey = normalizeKey(
                coverflowCards[currentIndex].getAttribute("data-diet-key") ||
                coverflowCards[currentIndex].getAttribute("data-dietkey")
            );

            dietFilterButtons.forEach(button => {
                const buttonDiet = normalizeKey(button.getAttribute("data-diet"));
                if (buttonDiet === currentDietKey) {
                    button.classList.add("active");
                } else {
                    button.classList.remove("active");
                }
            });
        }

        // Next and Prev buttons to navigate the coverflow
        if (dietNextButton) {
            dietNextButton.addEventListener("click", () => {
                updateCoverflow(currentIndex + 1);
            });
        }

        if (dietPrevButton) {
            dietPrevButton.addEventListener("click", () => {
                updateCoverflow(currentIndex - 1);
            });
        }

        // Click directly on the tabs on either side to rotate to that tab
        coverflowCards.forEach((card, index) => {
            card.addEventListener("click", (e) => {
                if (e.target.closest("a, button") && card.classList.contains("active")) {
                    return;
                }
                updateCoverflow(index);
            });
        });

        // Click button Diet Chip to change
        dietFilterButtons.forEach(button => {
            button.addEventListener("click", function (e) {
                if (coverflowCards.length === 0 || this.tagName.toLowerCase() === 'a') return;
                const selectedDiet = normalizeKey(this.getAttribute("data-diet"));

                let targetIndex = -1;
                coverflowCards.forEach((card, index) => {
                    const cardKey = normalizeKey(
                        card.getAttribute("data-diet-key") ||
                        card.getAttribute("data-dietkey")
                    );
                    if (cardKey === selectedDiet) {
                        targetIndex = index;
                    }
                });

                if (targetIndex !== -1) {
                    updateCoverflow(targetIndex);
                }
            });
        });

        updateCoverflow(0);
    }

    // Auto submit form on /recipes page when changing radio filters or dropdown
    const recipeSearchForm = document.querySelector('.search-bar-container');
    if (recipeSearchForm) {
        const recipeRadios = recipeSearchForm.querySelectorAll('.diet-radio');
        const categorySelect = recipeSearchForm.querySelector('.category-select');

        recipeRadios.forEach(radio => {
            radio.addEventListener('change', function () {
                recipeSearchForm.submit();
            });
        });

        if (categorySelect) {
            categorySelect.addEventListener('change', function () {
                recipeSearchForm.submit();
            });
        }
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
    function initLoadMore() {
        const loadMoreButton = document.getElementById('load-more-button');
        if (!loadMoreButton) return;

        // Xóa các event cũ để tránh bị gắn lặp
        const newBtn = loadMoreButton.cloneNode(true);
        loadMoreButton.parentNode.replaceChild(newBtn, loadMoreButton);

        const urlParams = new URLSearchParams(window.location.search);
        let currentPage = parseInt(urlParams.get('page')) || 1;

        newBtn.addEventListener('click', function () {
            currentPage++;

            const currentParams = new URLSearchParams(window.location.search);
            currentParams.set('page', currentPage);

            const url = new URL(window.location.href);
            url.search = currentParams.toString();
            const newUrl = url.pathname + url.search;

            newBtn.classList.add('loading');
            newBtn.disabled = true;

            fetch(newUrl)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');

                    // Lấy toàn bộ card mới từ trang vừa fetch về
                    let newCards = doc.querySelectorAll('#recipe-container .recipe-card-link');
                    const container = document.getElementById('recipe-container');

                    if (newCards.length > 0 && container) {
                        newCards.forEach(card => container.appendChild(card));

                        const totalVisibleCards = container.querySelectorAll('.recipe-card-link').length;
                        const countElement = document.getElementById('displayed-count');
                        if (countElement) {
                            countElement.innerText = totalVisibleCards;
                        }

                        window.history.replaceState({ page: currentPage }, '', newUrl);

                        // Cập nhật khung chứa nút Load More bằng HTML mới vừa fetch
                        const newLoadMoreWrapper = doc.querySelector('.load-more-wrapper');
                        const currentLoadMoreWrapper = document.querySelector('.load-more-wrapper');
                        if (newLoadMoreWrapper && currentLoadMoreWrapper) {
                            currentLoadMoreWrapper.innerHTML = newLoadMoreWrapper.innerHTML;
                            // Re-init listener cho nút Load More mới
                            initLoadMore();
                        }
                    } else {
                        newBtn.parentElement.innerHTML = '<div class="reached-end-badge"><span class="end-icon">✨</span><span>You\'ve reached the end of the list!</span></div>';
                    }
                })
                .catch(err => {
                    console.error("Error loading more recipes:", err);
                    newBtn.classList.remove('loading');
                    newBtn.disabled = false;
                });
        });
    }

    initLoadMore();

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
window.addEventListener("pageshow", function (e) {
    if (e.persisted || (window.performance && window.performance.navigation.type === 2)) {
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
    }
});