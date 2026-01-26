(() => {
    'use strict';

    let selectedDate = leaderboardConfig.currentDateIso;
    let leaderboardData = [];
    let isLoading = false;
    let sortColumn = 'place';
    let sortDirection = 'asc';

    const leaderboardBody = document.getElementById('leaderboard-body');
    const tableWrapper = document.getElementById('leaderboard-table-wrapper');
    const emptyState = document.getElementById('empty-state');
    const dateInput = document.getElementById('date-picker');
    const sortHeaders = document.querySelectorAll('.leaderboard-th[data-sort]');

    // Initialize date picker value
    if (dateInput) {
        dateInput.value = leaderboardConfig.currentDateFormatted;
        
        // Create hidden date input for native date picker
        const hiddenDateInput = document.createElement('input');
        hiddenDateInput.type = 'date';
        hiddenDateInput.style.position = 'absolute';
        hiddenDateInput.style.opacity = '0';
        hiddenDateInput.style.pointerEvents = 'none';
        hiddenDateInput.min = leaderboardConfig.minDateIso;
        hiddenDateInput.max = leaderboardConfig.maxDateIso;
        hiddenDateInput.value = leaderboardConfig.currentDateIso;
        dateInput.parentElement.appendChild(hiddenDateInput);

        dateInput.addEventListener('click', () => {
            hiddenDateInput.showPicker();
        });

        hiddenDateInput.addEventListener('change', (e) => {
            const newDate = e.target.value;
            if (newDate && newDate !== selectedDate) {
                selectedDate = newDate;
                // Format the date for display
                const dateObj = new Date(newDate + 'T00:00:00');
                const options = { year: 'numeric', month: 'long', day: 'numeric' };
                dateInput.value = dateObj.toLocaleDateString('en-US', options);
                fetchLeaderboard();
            }
        });
    }

    // Escape HTML to prevent XSS
    const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    // Show loading state
    const showLoading = () => {
        leaderboardBody.innerHTML = `
            <tr>
                <td colspan="4">
                    <div class="leaderboard-loading">
                        <div class="leaderboard-spinner"></div>
                        <span class="leaderboard-loading-text">Loading leaderboard...</span>
                    </div>
                </td>
            </tr>
        `;
        tableWrapper.classList.remove('leaderboard-table-wrapper--hidden');
        emptyState.classList.remove('leaderboard-empty--visible');
    };

    // Sort data based on current column and direction
    const sortData = (data) => {
        const sorted = [...data];
        sorted.sort((a, b) => {
            let aVal, bVal;
            
            switch (sortColumn) {
                case 'place':
                    aVal = a.rank;
                    bVal = b.rank;
                    break;
                case 'player':
                    aVal = a.username.toLowerCase();
                    bVal = b.username.toLowerCase();
                    break;
                case 'time':
                    aVal = a.seconds;
                    bVal = b.seconds;
                    break;
                case 'moves':
                    aVal = a.moves;
                    bVal = b.moves;
                    break;
                default:
                    return 0;
            }

            if (typeof aVal === 'string') {
                const cmp = aVal.localeCompare(bVal);
                return sortDirection === 'asc' ? cmp : -cmp;
            }
            
            return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
        });
        return sorted;
    };

    // Update sort header UI
    const updateSortHeaders = () => {
        sortHeaders.forEach(th => {
            const column = th.dataset.sort;
            th.classList.remove('leaderboard-th--active', 'leaderboard-th--desc');
            if (column === sortColumn) {
                th.classList.add('leaderboard-th--active');
                if (sortDirection === 'desc') {
                    th.classList.add('leaderboard-th--desc');
                }
            }
        });
    };

    // Render a single row
    const renderRow = (entry, index, userRankInList) => {
        const isCurrentUser = leaderboardConfig.currentUserId && entry.userId === leaderboardConfig.currentUserId;
        const isTop3 = entry.rank <= 3;
        
        let rowClass = 'leaderboard-row';
        if (isTop3) rowClass += ' leaderboard-row--top3';
        if (isCurrentUser) rowClass += ' leaderboard-row--you';

        const placeDisplay = entry.rank <= 999 ? entry.rank : 'XXX';
        const playerName = isCurrentUser 
            ? `<span class="leaderboard-you-badge">(You)</span> ${escapeHtml(entry.username)}`
            : escapeHtml(entry.username);

        return `
            <tr class="${rowClass}" data-user-id="${entry.userId}">
                <td class="leaderboard-td leaderboard-td--place">${placeDisplay}</td>
                <td class="leaderboard-td leaderboard-td--player${isCurrentUser ? ' leaderboard-td--player-you' : ''}">${playerName}</td>
                <td class="leaderboard-td leaderboard-td--time">${entry.seconds}s</td>
                <td class="leaderboard-td leaderboard-td--moves">${entry.moves}</td>
            </tr>
        `;
    };

    // Render the leaderboard table
    const render = () => {
        if (leaderboardData.length === 0) {
            tableWrapper.classList.add('leaderboard-table-wrapper--hidden');
            emptyState.classList.add('leaderboard-empty--visible');
            return;
        }

        emptyState.classList.remove('leaderboard-empty--visible');
        tableWrapper.classList.remove('leaderboard-table-wrapper--hidden');

        // Assign ranks before sorting for display
        const dataWithRanks = leaderboardData.map((entry, index) => ({
            ...entry,
            rank: index + 1
        }));

        // Find user's rank
        const userRank = dataWithRanks.find(e => e.userId === leaderboardConfig.currentUserId)?.rank;

        // Sort data
        const sortedData = sortData(dataWithRanks);

        // Build table rows
        let html = '';
        let lastWasTop3 = false;

        sortedData.forEach((entry, index) => {
            const isTop3 = entry.rank <= 3;
            
            // Add separator after top 3 when sorted by place
            if (sortColumn === 'place' && sortDirection === 'asc' && lastWasTop3 && !isTop3) {
                html += `<tr class="leaderboard-row--separator"><td colspan="4"></td></tr>`;
            }
            
            html += renderRow(entry, index, userRank);
            lastWasTop3 = isTop3;
        });

        leaderboardBody.innerHTML = html;
        updateSortHeaders();
    };

    // Fetch leaderboard data from API
    const fetchLeaderboard = async () => {
        if (isLoading) return;
        isLoading = true;
        showLoading();

        try {
            const url = `/api/leaderboard/daily/${selectedDate}/`;
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to fetch leaderboard');
            }
            
            const data = await response.json();
            leaderboardData = data.entries || [];
        } catch (error) {
            console.error('Error fetching leaderboard:', error);
            leaderboardData = [];
        } finally {
            isLoading = false;
            render();
        }
    };

    // Sort header click handling
    sortHeaders.forEach((th) => {
        th.addEventListener('click', () => {
            const column = th.dataset.sort;
            
            if (column === sortColumn) {
                // Toggle direction
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                // New column, default direction
                sortColumn = column;
                sortDirection = 'asc';
            }
            
            render();
        });
    });

    // Initial fetch
    fetchLeaderboard();
})();
