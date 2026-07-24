document.getElementById("update-time").innerText = new Date().toLocaleString();

// Example: Inject news sentiment
const newsData = [
  {source: "Bloomberg", headline: "Fed hints at rate cuts", sentiment: "Bullish"},
  {source: "Reuters", headline: "Crypto ETF inflows surge", sentiment: "Bullish"},
  {source: "CoinDesk", headline: "Bitcoin whale transfers spike", sentiment: "Neutral"}
];

const newsTable = document.getElementById("news-table");
newsData.forEach(n => {
  const row = `<tr><td>${n.source}</td><td>${n.headline}</td><td>${n.sentiment}</td></tr>`;
  newsTable.innerHTML += row;
});
