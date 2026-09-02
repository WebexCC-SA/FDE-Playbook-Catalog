# Webex Contact Center Playbooks

Search public Webex Contact Center reference playbooks by use case, channel,
feature, customer journey, integration, and complexity. Published playbooks
have completed the catalog review process.

<div class="playbook-catalog">
  <label class="search-label" for="playbook-search">Search playbooks</label>
  <input
    id="playbook-search"
    class="playbook-search"
    type="search"
    placeholder="Search by title, summary, feature, or keyword"
    autocomplete="off"
  >

  <div class="playbook-filters">
    <label>
      Vertical
      <select id="vertical-filter">
        <option value="">All verticals</option>
      </select>
    </label>

    <label>
      Channel
      <select id="channel-filter">
        <option value="">All channels</option>
      </select>
    </label>

    <label>
      Feature
      <select id="feature-filter">
        <option value="">All features</option>
      </select>
    </label>

    <label>
      Customer journey
      <select id="journey-filter">
        <option value="">All customer journeys</option>
      </select>
    </label>

    <label>
      Integration
      <select id="integration-filter">
        <option value="">All integrations</option>
      </select>
    </label>

    <label>
      Complexity
      <select id="complexity-filter">
        <option value="">All complexity levels</option>
      </select>
    </label>
  </div>

  <div class="catalog-actions">
    <p id="playbook-result-count" aria-live="polite">Loading playbooks…</p>
    <button id="clear-filters" type="button">Clear filters</button>
  </div>

  <div id="playbook-results" class="playbook-results"></div>

  <div id="playbook-empty-state" class="playbook-empty" hidden>
    <h2 id="playbook-empty-title">No matching playbooks</h2>
    <p id="playbook-empty-message">Try removing a filter or using a broader search term.</p>
  </div>
</div>
