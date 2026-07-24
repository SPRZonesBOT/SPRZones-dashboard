// Update timestamp
document.getElementById("update-time").innerText = new Date().toLocaleString();

// Fetch signals.json (market data + sentiment)
fetch('../data/signals.json')
  .then(response => response.json())
  .then(data => {
    // Macro Economics
    document.getElementById("us-yield").innerText = data.macro.us_yield;
    document.getElementById("dxy").innerText = data.macro.dxy;
    document.getElementById("crude").innerText = data.macro.crude;
    document.getElementById("fii-dii").innerText = data.macro.fii_dii;
    document.getElementById("fear-greed").innerText = data.macro.fear_greed;

    // News Sentiment Heatmap
    const newsTable = document.getElementById("news-table");
    newsTable.innerHTML = "";
    data.news.forEach(n => {
      const row = `<tr>
        <td>${n.source}</td>
        <td>${n.headline}</td>
        <td>${n.sentiment}</td>
      </tr>`;
      newsTable.innerHTML += row;
    });

    // Social Media Sentiment
    document.getElementById("twitter").innerText = data.social.twitter_mentions;
    document.getElementById("reddit").innerText = data.social.reddit_sentiment;

    // On-Chain Analytics
    document.getElementById("whale-inflows").innerText = data.onchain.whale_inflows;
    document.getElementById("stablecoin").innerText = data.onchain.stablecoin_activity;
    document.getElementById("exchange-reserves").innerText = data.onchain.exchange_reserves;

    // ETF & Fund Flows
    document.getElementById("gold-etf").innerText = data.etf.gold_flows;
    document.getElementById("btc-etf").innerText = data.etf.btc_flows;

    // Confluence Factors Table
    const confTable = document.querySelector("section:last-of-type tbody");
    confTable.innerHTML = "";
    data.confluence.forEach(c => {
      const row = `<tr>
        <td>${c.asset}</td>
        <td>${c.signal}</td>
        <td>${c.confidence}</td>
        <td>${c.bull}</td>
        <td>${c.bear}</td>
        <td>${c.verdict}</td>
        <td>${c.action}</td>
      </tr>`;
      confTable.innerHTML += row;
    });
  })
  .catch(err => console.error("Error loading signals.json:", err));
