function updateDashboard() {
  fetch('../data/signals.json')
    .then(response => response.json())
    .then(data => {
      // Timestamp
      document.getElementById("update-time").innerText = new Date().toLocaleString();

      // Macro
      document.getElementById("us-yield").innerText = data.macro.us_yield;
      document.getElementById("dxy").innerText = data.macro.dxy;
      document.getElementById("crude").innerText = data.macro.crude;
      document.getElementById("fii-dii").innerText = data.macro.fii_dii;
      document.getElementById("fear-greed").innerText = data.macro.fear_greed;

      // News
      const newsTable = document.getElementById("news-table");
      newsTable.innerHTML = "";
      data.news.forEach(n => {
        const row = `<tr><td>${n.source}</td><td>${n.headline}</td><td>${n.sentiment}</td></tr>`;
        newsTable.innerHTML += row;
      });

      // Social
      document.getElementById("twitter").innerText = data.social.twitter_mentions;
      document.getElementById("reddit").innerText = data.social.reddit_sentiment;

      // On-chain
      document.getElementById("whale-inflows").innerText = data.onchain.whale_inflows;
      document.getElementById("stablecoin").innerText = data.onchain.stablecoin_activity;
      document.getElementById("exchange-reserves").innerText = data.onchain.exchange_reserves;

      // ETF
      document.getElementById("gold-etf").innerText = data.etf.gold_flows;
      document.getElementById("btc-etf").innerText = data.etf.btc_flows;

      // Confluence
      const confTable = document.getElementById("confluence-table");
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

      // Charts
      // ETF Flows
      const etfCtx = document.getElementById('etfChart').getContext('2d');
      new Chart(etfCtx, {
        type: 'line',
        data: {
          labels: ["Week 1", "Week 2", "Week 3", "Week 4"],
          datasets: [
            {
              label: 'Gold ETF Flows',
              data: [1200, 800, 1500, 1000], // replace with historical data
              borderColor: 'gold',
              fill: false
            },
            {
              label: 'Bitcoin ETF Flows',
              data: [850, 900, 1100, 950], // replace with historical data
              borderColor: 'orange',
              fill: false
            }
          ]
        }
      });

      // Sentiment Distribution
      const sentimentCounts = { Bullish: 0, Neutral: 0, Bearish: 0 };
      data.news.forEach(n => sentimentCounts[n.sentiment]++);
      const sentimentCtx = document.getElementById('sentimentChart').getContext('2d');
      new Chart(sentimentCtx, {
        type: 'bar',
        data: {
          labels: ['Bullish', 'Neutral', 'Bearish'],
          datasets: [{
            label: 'News Sentiment',
            data: [sentimentCounts.Bullish, sentimentCounts.Neutral, sentimentCounts.Bearish],
            backgroundColor: ['green', 'gray', 'red']
          }]
        }
      });
    })
    .catch(err => console.error("Error loading signals.json:", err));
}

// Auto-refresh every 5 minutes
updateDashboard();
setInterval(updateDashboard, 300000);
