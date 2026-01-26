(() => {
    'use strict';

    let activeTab = 'daily';
    let expandedId = null;
    let searchQuery = '';

    const puzzleList = document.getElementById('puzzle-list');
    const puzzleListWrapper = document.getElementById('puzzle-list-wrapper');
    const emptyState = document.getElementById('empty-state');
    const searchInput = document.getElementById('search-date');
    const tabs = document.querySelectorAll('.profile-tab');

    // Check if list is scrollable and update wrapper class
    const checkScrollable = () => {
        if (!puzzleList || !puzzleListWrapper) return;
        
        const isScrollable = puzzleList.scrollHeight > puzzleList.clientHeight;
        const isAtBottom = puzzleList.scrollTop + puzzleList.clientHeight >= puzzleList.scrollHeight - 10;
        
        if (isScrollable && !isAtBottom) {
            puzzleListWrapper.classList.add('has-scroll');
        } else {
            puzzleListWrapper.classList.remove('has-scroll');
        }
    };

    // Find the best attempt in a list (lowest moves, then lowest time)
    const findBestAttemptId = (attempts) => {
        if (!attempts || attempts.length === 0) return -1;
        let bestIdx = 0;
        for (let i = 1; i < attempts.length; i++) {
            if (
                attempts[i].moves < attempts[bestIdx].moves ||
                (attempts[i].moves === attempts[bestIdx].moves &&
                    attempts[i].seconds < attempts[bestIdx].seconds)
            ) {
                bestIdx = i;
            }
        }
        return attempts[bestIdx].id;
    };

    // Filter puzzles by search query
    const filterPuzzles = (puzzles) => {
        if (!searchQuery) return puzzles;
        const query = searchQuery.toLowerCase().trim();
        return puzzles.filter((puzzle) =>
            puzzle.date.toLowerCase().includes(query) ||
            (puzzle.dateRaw && puzzle.dateRaw.includes(query)) ||
            (puzzle.name && puzzle.name.toLowerCase().includes(query))
        );
    };

    // Create rotate icon SVG
    const rotateIcon = () => `
        <svg class="profile-stat-icon" width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M11.0833 7.58333C11.0833 9.65437 9.40437 11.3333 7.33333 11.3333C5.26229 11.3333 3.58333 9.65437 3.58333 7.58333C3.58333 5.51229 5.26229 3.83333 7.33333 3.83333H9.33333M9.33333 3.83333L7.91667 2.41667M9.33333 3.83333L7.91667 5.25" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    `;

    // Create clock icon SVG
    const clockIcon = () => `
        <svg class="profile-stat-icon" width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <circle cx="7" cy="7" r="5.25" stroke="currentColor" stroke-width="1.25"/>
            <path d="M7 4.08333V7L8.75 8.75" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    `;

    // Render a single puzzle entry
    const renderEntry = (puzzle) => {
        const isExpanded = expandedId === puzzle.id;
        const bestAttemptId = findBestAttemptId(puzzle.attempts);

        const attemptsHtml = puzzle.attempts.map((attempt) => {
            const isBest = attempt.id === bestAttemptId;
            return `
                <div class="profile-attempt${isBest ? ' profile-attempt--best' : ''}">
                    <span class="profile-attempt-number">${attempt.id}.</span>
                    <span class="profile-attempt-stat">
                        ${rotateIcon()}
                        ${attempt.moves} Moves
                    </span>
                    <span class="profile-attempt-stat">
                        ${clockIcon()}
                        ${attempt.seconds} Seconds
                    </span>
                    ${isBest ? '<span class="profile-attempt-badge">Best result</span>' : ''}
                </div>
            `;
        }).join('');

        const displayDate = puzzle.name || puzzle.date;

        return `
            <div class="profile-entry${isExpanded ? ' profile-entry--expanded' : ''}" data-id="${puzzle.id}">
                <button
                    class="profile-entry-header"
                    type="button"
                    data-toggle="${puzzle.id}"
                    aria-expanded="${isExpanded}"
                >
                    <div class="profile-entry-info">
                        <span class="profile-entry-date">${displayDate}</span>
                        <div class="profile-entry-best">
                            <span class="profile-entry-label">Best result:</span>
                            <span class="profile-entry-stat">
                                ${rotateIcon()}
                                ${puzzle.bestMoves} Moves
                            </span>
                            <span class="profile-entry-stat">
                                ${clockIcon()}
                                ${puzzle.bestSeconds} Seconds
                            </span>
                        </div>
                    </div>
                    <svg class="profile-entry-chevron" width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                        <path d="M4.5 6.75L9 11.25L13.5 6.75" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
                <div class="profile-attempts">
                    ${attemptsHtml}
                </div>
            </div>
        `;
    };

    // Render the puzzle list
    const render = () => {
        const puzzles = (typeof puzzleData !== 'undefined' && puzzleData[activeTab]) ? puzzleData[activeTab] : [];
        const filtered = filterPuzzles(puzzles);

        console.log('render:', activeTab, 'puzzles:', puzzles.length, 'filtered:', filtered.length);

        if (filtered.length === 0) {
            puzzleList.innerHTML = '';
            puzzleList.style.display = 'none';
            puzzleListWrapper.style.display = 'none';
            emptyState.style.display = 'flex';
        } else {
            emptyState.style.display = 'none';
            puzzleListWrapper.style.display = 'block';
            puzzleList.style.display = 'flex';
            puzzleList.innerHTML = filtered.map(renderEntry).join('');
        }

        // Attach click handlers for expand/collapse
        puzzleList.querySelectorAll('[data-toggle]').forEach((btn) => {
            btn.addEventListener('click', () => {
                const id = btn.getAttribute('data-toggle');
                expandedId = expandedId === id ? null : id;
                render();
            });
        });

        // Check if scrollable after render
        setTimeout(checkScrollable, 50);
    };

    // Update tab ARIA attributes
    const updateTabAria = () => {
        tabs.forEach((tab) => {
            const isActive = tab.classList.contains('profile-tab--active');
            tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });
    };

    // Tab switching
    tabs.forEach((tab) => {
        tab.addEventListener('click', () => {
            const tabName = tab.getAttribute('data-tab');
            if (tabName === activeTab) return;

            activeTab = tabName;
            expandedId = null;

            // Update active tab style
            tabs.forEach((t) => t.classList.remove('profile-tab--active'));
            tab.classList.add('profile-tab--active');
            updateTabAria();

            render();
        });

        // Keyboard navigation for tabs
        tab.addEventListener('keydown', (e) => {
            const tabsArray = Array.from(tabs);
            const currentIndex = tabsArray.indexOf(tab);

            if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                e.preventDefault();
                const direction = e.key === 'ArrowRight' ? 1 : -1;
                const nextIndex = (currentIndex + direction + tabsArray.length) % tabsArray.length;
                tabsArray[nextIndex].focus();
                tabsArray[nextIndex].click();
            }
        });
    });

    // Search input with debounce
    let searchTimeout;
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchQuery = e.target.value;
                render();
            }, 150);
        });

        // Clear search on Escape
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && searchQuery) {
                e.preventDefault();
                searchInput.value = '';
                searchQuery = '';
                render();
            }
        });
    }

    // Listen for scroll events on the list
    if (puzzleList) {
        puzzleList.addEventListener('scroll', checkScrollable);
    }

    // Check on window resize
    window.addEventListener('resize', checkScrollable);

    // Initial render
    render();
})();
