// Restaurant Search Web App - Frontend Logic

console.log('[App] Application initialized');

// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const loading = document.getElementById('loading');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const resultsSection = document.getElementById('resultsSection');
const detailSearchButton = document.getElementById('detailSearchButton');
const detailLoading = document.getElementById('detailLoading');
const detailLoadingText = document.getElementById('detailLoadingText');
const step4Container = document.getElementById('step4Container');
const step5Container = document.getElementById('step5Container');

// State
let currentSearchResult = null;

// Event Listeners
searchButton.addEventListener('click', handleSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSearch();
    }
});
detailSearchButton.addEventListener('click', handleDetailSearch);

/**
 * Handle initial search
 */
async function handleSearch() {
    const inputText = searchInput.value.trim();

    console.log('[Search] Button clicked');
    console.log('[Search] Input text:', inputText);

    // Validation
    if (!inputText) {
        showError('検索条件を入力してください');
        return;
    }

    // Reset UI
    hideError();
    hideResults();
    showLoading();
    searchButton.disabled = true;

    try {
        console.log('[API] Calling POST /api/search');
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ input_text: inputText })
        });

        console.log('[API] Response status:', response.status);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'API request failed');
        }

        const data = await response.json();
        console.log('[API] Response data:', data);

        // Store result
        currentSearchResult = data;

        // Display results
        displayResults(data);

    } catch (error) {
        console.error('[Search] Error:', error);
        showError(`検索エラー: ${error.message}`);
    } finally {
        hideLoading();
        searchButton.disabled = false;
    }
}

/**
 * Display search results (Steps 1-3)
 */
function displayResults(data) {
    console.log('[Display] Rendering results');

    // Step 1: Input Details
    document.getElementById('step1InputText').textContent = data.input_text;
    document.getElementById('step1Prompt').textContent = data.prompt_used;
    document.getElementById('step1Model').textContent = data.model_name;

    console.log('[Display] Step 1 rendered');

    // Step 2: Initial Search Results
    document.getElementById('step2RawResponse').textContent = data.raw_response;
    document.getElementById('step2Metadata').textContent = JSON.stringify(data.grounding_metadata, null, 2);

    console.log('[Display] Step 2 rendered');

    // Step 3: Shop List
    const shopList = document.getElementById('shopList');
    shopList.innerHTML = '';

    data.shop_list.shops.forEach((shop, index) => {
        const li = document.createElement('li');
        li.className = 'shop-item';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `shop-${index}`;
        checkbox.value = shop;

        const label = document.createElement('label');
        label.htmlFor = `shop-${index}`;
        label.textContent = shop;

        li.appendChild(checkbox);
        li.appendChild(label);
        shopList.appendChild(li);
    });

    console.log('[Display] Step 3 rendered with', data.shop_list.shops.length, 'shops');

    // Setup checkbox listeners
    setupCheckboxListeners();

    // Show results section
    showResults();
}

/**
 * Setup checkbox change listeners
 */
function setupCheckboxListeners() {
    const checkboxes = document.querySelectorAll('#shopList input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateDetailSearchButton);
    });
    updateDetailSearchButton();
}

/**
 * Update detail search button visibility based on checkbox selection
 */
function updateDetailSearchButton() {
    const checkboxes = document.querySelectorAll('#shopList input[type="checkbox"]');
    const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;

    if (checkedCount > 0) {
        detailSearchButton.style.display = 'inline-block';
        console.log('[UI] Detail search button shown:', checkedCount, 'shops selected');
    } else {
        detailSearchButton.style.display = 'none';
        console.log('[UI] Detail search button hidden: no shops selected');
    }
}

/**
 * Handle detail search for selected shops
 */
async function handleDetailSearch() {
    console.log('[Detail Search] Button clicked');

    // Get selected shops
    const checkboxes = document.querySelectorAll('#shopList input[type="checkbox"]:checked');
    const selectedShops = Array.from(checkboxes).map(cb => cb.value);

    console.log('[Detail Search] Selected shops:', selectedShops);

    if (selectedShops.length === 0) {
        showError('店舗を選択してください');
        return;
    }

    // Reset UI
    hideError();
    step4Container.innerHTML = '';
    step4Container.classList.add('hidden');
    step5Container.classList.add('hidden');
    detailLoading.classList.add('active');
    detailSearchButton.disabled = true;

    try {
        console.log('[API] Calling POST /api/search/detail');
        const response = await fetch('/api/search/detail', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input_text: currentSearchResult.input_text,
                shop_names: selectedShops
            })
        });

        console.log('[API] Response status:', response.status);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'API request failed');
        }

        const data = await response.json();
        console.log('[API] Response data:', data);

        // Display detail results
        displayDetailResults(data);

    } catch (error) {
        console.error('[Detail Search] Error:', error);
        showError(`個別店舗検索エラー: ${error.message}`);
    } finally {
        detailLoading.classList.remove('active');
        detailSearchButton.disabled = false;
    }
}

/**
 * Display detail search results (Steps 4-5)
 */
function displayDetailResults(data) {
    console.log('[Display] Rendering detail results');

    // Step 4: Individual shop details
    step4Container.innerHTML = '';

    data.summaries.forEach((summary, index) => {
        const stepBox = document.createElement('div');
        stepBox.className = 'step-box';

        const stepHeader = document.createElement('div');
        stepHeader.className = 'step-header';
        stepHeader.onclick = () => toggleCollapse(`step4-${index}-content`);

        const icon = document.createElement('span');
        icon.className = 'collapse-icon';
        icon.id = `step4-${index}-icon`;
        icon.textContent = '▼';

        const heading = document.createElement('h3');
        heading.textContent = `Step 4-${index + 1}: ${summary.shop_name} の詳細サーチ結果`;

        stepHeader.appendChild(icon);
        stepHeader.appendChild(heading);

        const stepContent = document.createElement('div');
        stepContent.className = 'step-content';
        stepContent.id = `step4-${index}-content`;

        const infoGrid = document.createElement('div');
        infoGrid.className = 'info-grid';
        infoGrid.innerHTML = `
            <div class="info-label">店舗名:</div>
            <div class="info-value">${summary.shop_name}</div>

            <div class="info-label">サーチ結果:</div>
            <div class="info-value">
                <div class="text-box">${summary.detail_search_result}</div>
            </div>

            <div class="info-label">合致度スコア:</div>
            <div class="info-value">
                <span class="score-badge score-${summary.judgement.score}">${summary.judgement.score}</span>
            </div>

            <div class="info-label">判定理由:</div>
            <div class="info-value">${summary.judgement.reason}</div>
        `;

        stepContent.appendChild(infoGrid);
        stepBox.appendChild(stepHeader);
        stepBox.appendChild(stepContent);
        step4Container.appendChild(stepBox);
    });

    step4Container.classList.remove('hidden');
    console.log('[Display] Step 4 rendered with', data.summaries.length, 'shops');

    // Step 5: Summary table
    const tableBody = document.getElementById('summaryTableBody');
    tableBody.innerHTML = '';

    data.summaries.forEach(summary => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${summary.shop_name}</td>
            <td><span class="score-badge score-${summary.judgement.score}">${summary.judgement.score}</span></td>
            <td>${summary.judgement.reason}</td>
        `;
        tableBody.appendChild(row);
    });

    step5Container.classList.remove('hidden');
    console.log('[Display] Step 5 rendered with summary table');
}

/**
 * Toggle collapse state
 */
function toggleCollapse(contentId) {
    const content = document.getElementById(contentId);
    const iconId = contentId.replace('Content', 'Icon');
    const icon = document.getElementById(iconId);

    content.classList.toggle('collapsed');
    icon.textContent = content.classList.contains('collapsed') ? '▶' : '▼';

    console.log('[UI] Toggled collapse:', contentId);
}

/**
 * UI Helper Functions
 */
function showLoading() {
    loading.classList.add('active');
    console.log('[UI] Loading shown');
}

function hideLoading() {
    loading.classList.remove('active');
    console.log('[UI] Loading hidden');
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.classList.add('active');
    console.error('[UI] Error shown:', message);
}

function hideError() {
    errorMessage.classList.remove('active');
    console.log('[UI] Error hidden');
}

function showResults() {
    resultsSection.classList.remove('hidden');
    console.log('[UI] Results shown');
}

function hideResults() {
    resultsSection.classList.add('hidden');
    console.log('[UI] Results hidden');
}

// Debug: Log all console messages
console.log('[App] Ready for user interaction');
