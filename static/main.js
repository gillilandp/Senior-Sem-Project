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

        // Delete old events to avoid duplicate bindings
        const newButton = loadMoreButton.cloneNode(true);
        loadMoreButton.parentNode.replaceChild(newButton, loadMoreButton);

        newButton.addEventListener('click', function () {
            const urlParams = new URLSearchParams(window.location.search);
            let currentPage = parseInt(urlParams.get('page')) || 1;
            currentPage++;

            const currentParams = new URLSearchParams(window.location.search);
            currentParams.set('page', currentPage);

            const url = new URL(window.location.href);
            url.search = currentParams.toString();
            const newUrl = url.pathname + url.search;

            newButton.classList.add('loading');
            newButton.disabled = true;

            fetch(newUrl)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');

                    // Get all new cards from the fetched page
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

                        // Update the Load More button wrapper with the newly fetched HTML
                        const newLoadMoreWrapper = doc.querySelector('.load-more-wrapper');
                        const currentLoadMoreWrapper = document.querySelector('.load-more-wrapper');
                        if (newLoadMoreWrapper && currentLoadMoreWrapper) {
                            currentLoadMoreWrapper.innerHTML = newLoadMoreWrapper.innerHTML;
                            // Re-init listener for the new Load More button
                            initLoadMore();
                        }
                    } else {
                        const currentLoadMoreWrapper = document.querySelector('.load-more-wrapper');
                        if (currentLoadMoreWrapper) {
                            currentLoadMoreWrapper.innerHTML = '<div class="reached-end-badge"><span class="end-icon">✨</span><span>You\'ve reached the end of the list!</span></div>';
                        }
                    }
                })
                .catch(err => {
                    console.error("Error loading more recipes:", err);
                    newButton.classList.remove('loading');
                    newButton.disabled = false;
                });
        });
    }

    initLoadMore();

    // 4b) Load More Grocery Products Button
    function initGroceryLoadMore() {
        const loadMoreBtn = document.getElementById('load-more-grocery-btn');
        const container = document.getElementById('grocery-container');
        const wrapper = document.getElementById('grocery-load-more-wrapper');

        if (!loadMoreBtn || !container || !wrapper) return;

        loadMoreBtn.addEventListener('click', async function () {
            const currentPage = parseInt(this.getAttribute('data-page')) || 1;
            const nextPage = currentPage + 1;
            const query = this.getAttribute('data-query') || '';
            const searchType = this.getAttribute('data-type') || new URLSearchParams(window.location.search).get('type') || 'product';

            loadMoreBtn.disabled = true;
            loadMoreBtn.querySelector('span').textContent = 'Loading...';

            try {
                const url = '/grocery?q=' + encodeURIComponent(query) + '&type=' + encodeURIComponent(searchType) + '&page=' + nextPage + '&ajax=1';
                const response = await fetch(url);
                const data = await response.json();

                data.products.forEach(function (item) {
                    const card = document.createElement('div');
                    card.className = 'recipe-card-detailed';

                    // Create the image wrapper
                    const imgWrapper = document.createElement('div');
                    imgWrapper.className = 'card-img-wrapper';
                    imgWrapper.style.cssText = 'display:flex; align-items:center; justify-content:center; background:#ffffff; height:190px; padding:12px; border-bottom:1px solid #f1f5f9;';

                    if (item.image_url) {
                        const img = document.createElement('img');
                        img.src = item.image_url;
                        img.alt = item.product_name || '';
                        img.style.cssText = 'width:auto !important; height:auto !important; max-width:100%; max-height:165px; object-fit:contain !important;';
                        img.onerror = function () {
                            card.style.display = 'none';
                        };
                        imgWrapper.appendChild(img);
                    } else {
                        const placeholder = document.createElement('div');
                        placeholder.style.fontSize = '42px';
                        placeholder.textContent = '📦';
                        imgWrapper.appendChild(placeholder);
                    }

                    // Create the card body
                    const cardBody = document.createElement('div');
                    cardBody.className = 'card-body';

                    const brandSpan = document.createElement('span');
                    brandSpan.className = 'sub-caption';
                    brandSpan.textContent = item.brands || '';

                    const titleH3 = document.createElement('h3');
                    titleH3.className = 'recipe-name';
                    titleH3.style.cssText = 'min-height: 48px; margin-bottom: 8px; font-size: 15px;';
                    titleH3.textContent = item.product_name || '';

                    const metaDiv = document.createElement('div');
                    metaDiv.className = 'recipe-meta';
                    metaDiv.style.marginTop = 'auto';

                    if (item.labels) {
                        const shortLabels = item.labels.length > 50 ? item.labels.substring(0, 50) + '...' : item.labels;
                        const labelP = document.createElement('p');
                        labelP.style.cssText = 'font-size: 11px; color: #2e7d32; margin-bottom: 4px;';
                        labelP.innerHTML = '<strong>Labels:</strong> ';
                        labelP.appendChild(document.createTextNode(shortLabels));
                        metaDiv.appendChild(labelP);
                    }

                    const allergenP = document.createElement('p');
                    if (item.allergens) {
                        allergenP.style.cssText = 'font-size: 11px; color: #c62828;';
                        allergenP.innerHTML = '<strong>Allergens:</strong> ';
                        allergenP.appendChild(document.createTextNode(item.allergens));
                    } else {
                        allergenP.style.cssText = 'font-size: 11px; color: #718096;';
                        allergenP.innerHTML = '<strong>Allergens:</strong> No allergens listed';
                    }
                    metaDiv.appendChild(allergenP);

                    cardBody.appendChild(brandSpan);
                    cardBody.appendChild(titleH3);
                    cardBody.appendChild(metaDiv);

                    card.appendChild(imgWrapper);
                    card.appendChild(cardBody);
                    container.appendChild(card);
                });

                const countEl = document.getElementById('displayed-count');
                if (countEl) {
                    countEl.textContent = container.children.length;
                }

                if (data.has_more) {
                    loadMoreBtn.setAttribute('data-page', nextPage);
                    loadMoreBtn.disabled = false;
                    loadMoreBtn.querySelector('span').textContent = 'Load More Products';
                } else {
                    wrapper.innerHTML = '<div class="reached-end-badge"><span class="end-icon">✨</span><span>You\'ve reached the end of the list!</span></div>';
                }
            } catch (err) {
                console.error('Failed to load more products:', err);
                loadMoreBtn.disabled = false;
                loadMoreBtn.querySelector('span').textContent = 'Load More Products';
            }
        });
    }

    initGroceryLoadMore();

    // 5) Save the state before clicking on a card
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
    // 6) Auto-submit search form when clicking any filter chip including Matched My Profile
    const dietCheckboxes = document.querySelectorAll('.quick-diet-filters .diet-checkbox');
    const searchForm = document.getElementById('recipeSearchForm');

    if (dietCheckboxes.length > 0 && searchForm) {
        dietCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function () {
                // If clicking the "Matched My Profile" button, uncheck other individual diet buttons
                if (this.name === 'match_profile' && this.checked) {
                    const dietInputs = document.querySelectorAll('input[name="diet"]');
                    dietInputs.forEach(input => input.checked = false);
                }

                // If clicking any individual diet button, uncheck "Matched My Profile"
                if (this.name === 'diet' && this.checked && this.value !== 'all') {
                    const matchInput = document.querySelector('input[name="match_profile"]');
                    if (matchInput) {
                        matchInput.checked = false;
                    }
                }

            });
        });
    }
});


// 7) Restore State when clicking "GO BACK" and Return to the previous page (recipes.html or main.html) 
window.addEventListener("pageshow", function (e) {
    if (e.persisted || (window.performance && window.performance.navigation.type === 2)) {
        const pageKey = window.location.pathname;

        // 7a. Restore the list of items loaded via "Load More" and the item count
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

        // 7b. Restore the horizontal scroll position of the carousel (main.html)
        const track = document.querySelector(".carousel-track-container");
        const savedTrackScrollLeft = sessionStorage.getItem(pageKey + '_trackScrollLeft');
        if (track && savedTrackScrollLeft !== null) {
            track.scrollLeft = parseInt(savedTrackScrollLeft, 10);
            sessionStorage.removeItem(pageKey + '_trackScrollLeft');
        }

        // 7c. Restore vertical page scroll position
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