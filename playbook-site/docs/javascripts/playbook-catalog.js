document.addEventListener("DOMContentLoaded", async () => {
  const search = document.querySelector("#playbook-search");
  const results = document.querySelector("#playbook-results");
  const resultCount = document.querySelector("#playbook-result-count");
  const emptyState = document.querySelector("#playbook-empty-state");
  const clearButton = document.querySelector("#clear-filters");

  const filters = {
    verticals: {
      element: document.querySelector("#vertical-filter"),
      facet: "verticals",
    },
    channels: {
      element: document.querySelector("#channel-filter"),
      facet: "channels",
    },
    features: {
      element: document.querySelector("#feature-filter"),
      facet: "features",
    },
    customerJourneys: {
      element: document.querySelector("#journey-filter"),
      facet: "customer_journeys",
    },
    integrations: {
      element: document.querySelector("#integration-filter"),
      facet: "integrations",
    },
    complexity: {
      element: document.querySelector("#complexity-filter"),
      facet: "complexity",
    },
  };

  const labelFor = (value) =>
    value
      .split("-")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");

  try {
    const response = await fetch("data/playbooks.json");
    if (!response.ok) {
      throw new Error(`Catalog request failed: ${response.status}`);
    }

    const catalog = await response.json();
    const playbooks = catalog.playbooks || [];

    for (const filter of Object.values(filters)) {
      for (const value of catalog.facets[filter.facet] || []) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = labelFor(value);
        filter.element.appendChild(option);
      }
    }

    const matches = (playbook) => {
      const terms = search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      const searchableText = [
        playbook.title,
        playbook.summary,
        ...(playbook.verticals || []),
        ...(playbook.channels || []),
        ...(playbook.features || []),
        ...(playbook.customerJourneys || []),
        ...(playbook.integrations || []),
        ...(playbook.keywords || []),
      ]
        .join(" ")
        .toLowerCase();

      if (!terms.every((term) => searchableText.includes(term))) {
        return false;
      }

      return Object.entries(filters).every(([field, filter]) => {
        const selected = filter.element.value;
        if (!selected) {
          return true;
        }
        return field === "complexity"
          ? playbook.complexity === selected
          : (playbook[field] || []).includes(selected);
      });
    };

    const render = () => {
      const matchingPlaybooks = playbooks.filter(matches);
      resultCount.textContent = `${matchingPlaybooks.length} playbook${
        matchingPlaybooks.length === 1 ? "" : "s"
      } found`;
      results.replaceChildren();
      emptyState.hidden = matchingPlaybooks.length !== 0;

      for (const playbook of matchingPlaybooks) {
        const card = document.createElement("article");
        card.className = "playbook-card";

        const title = document.createElement("h2");
        title.textContent = playbook.title;

        const summary = document.createElement("p");
        summary.textContent = playbook.summary;

        const badges = document.createElement("div");
        badges.className = "playbook-badges";
        for (const value of [
          ...(playbook.verticals || []),
          ...(playbook.channels || []),
          ...(playbook.features || []),
        ]) {
          const badge = document.createElement("span");
          badge.className = "playbook-badge";
          badge.textContent = labelFor(value);
          badges.appendChild(badge);
        }
        if (playbook.requiresRebinding) {
          const badge = document.createElement("span");
          badge.className = "playbook-badge playbook-badge--warning";
          badge.textContent = "Rebinding required";
          badges.appendChild(badge);
        }

        const metadata = document.createElement("p");
        metadata.className = "playbook-meta";
        metadata.textContent = `${labelFor(playbook.complexity)} · Catalog reviewed ${
          playbook.lastValidated
        }`;

        const link = document.createElement("a");
        link.className = "playbook-link";
        link.href = playbook.url;
        link.textContent = "View playbook →";

        card.append(title, summary, badges, metadata, link);
        results.appendChild(card);
      }
    };

    search.addEventListener("input", render);
    for (const filter of Object.values(filters)) {
      filter.element.addEventListener("change", render);
    }
    clearButton.addEventListener("click", () => {
      search.value = "";
      for (const filter of Object.values(filters)) {
        filter.element.value = "";
      }
      render();
      search.focus();
    });

    render();
  } catch (error) {
    console.error(error);
    resultCount.textContent = "The playbook catalog could not be loaded.";
    emptyState.hidden = false;
  }
});
