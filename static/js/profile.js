(() => {
    let activeTab = 'daily';
    let expandedId = null;
    let searchQuery = '';

    const puzzleList = document.getElementById('puzzle-list');
    const emptyState = document.getElementById('empty-state');
    const searchInput = document.getElementById('search-date');
    const tabs = document.querySelectorAll('.profile-tab');

    // Find the best attempt in a list
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
        const query = searchQuery.toLowerCase();
        return puzzles.filter((puzzle) =>
            puzzle.date.toLowerCase().includes(query) ||
            puzzle.dateRaw.includes(query)
        );
    };

    // Render a single puzzle entry
    const renderEntry = (puzzle) => {
        const isExpanded = expandedId === puzzle.id;
        const bestAttemptId = findBestAttemptId(puzzle.attempts);

        const attemptsHtml = puzzle.attempts.map((attempt) => {
            const isBest = attempt.id === bestAttemptId;
            return `
                <div class="profile-attempt ${isBest ? 'profile-attempt--best' : ''}">
                    <span class="profile-attempt-number">${attempt.id}.</span>
                    <span class="profile-attempt-stat">
                        <i class="fa-solid fa-rotate profile-stat-icon" aria-hidden="true"></i>
                        ${attempt.moves} Moves
                    </span>
                    <span class="profile-attempt-stat">
                        <i class="fa-regular fa-clock profile-stat-icon" aria-hidden="true"></i>
                        ${attempt.seconds} Seconds
                    </span>
                    ${isBest ? '<span class="profile-attempt-badge">Best result</span>' : ''}
                </div>
            `;
        }).join('');

        return `
            <div class="profile-entry ${isExpanded ? 'profile-entry--expanded' : ''}" data-id="${puzzle.id}">
                <button class="profile-entry-header" type="button" data-toggle="${puzzle.id}">
                    <div class="profile-entry-info">
                        <span class="profile-entry-date">${puzzle.date}</span>
                        <div class="profile-entry-best">
                            <span class="profile-entry-label">Best result:</span>
                            <span class="profile-entry-stat">
                                <i class="fa-solid fa-rotate profile-stat-icon" aria-hidden="true"></i>
                                ${puzzle.bestMoves} Moves
                            </span>
                            <span class="profile-entry-stat">
                                <i class="fa-regular fa-clock profile-stat-icon" aria-hidden="true"></i>
                                ${puzzle.bestSeconds} Seconds
                            </span>
                        </div>
                    </div>
                    <i class="fa-solid fa-chevron-down profile-entry-chevron" aria-hidden="true"></i>
                </button>
                <div class="profile-attempts">
                    ${attemptsHtml}
                </div>
            </div>
        `;
    };

    // Render the puzzle list
    const render = () => {
        const puzzles = puzzleData[activeTab] || [];
        const filtered = filterPuzzles(puzzles);

        if (filtered.length === 0) {
            puzzleList.innerHTML = '';
            puzzleList.style.display = 'none';
            emptyState.style.display = 'flex';
        } else {
            emptyState.style.display = 'none';
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

            render();
        });
    });

    // Search input
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value;
            render();
        });
    }

    // Initial render
    render();
})();
