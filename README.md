# The G-Trendalyser 2.0 🐍🔥

The G-Trendalyser 2.0 is a web app that allows you to get up to 125 trending keywords from an input of just 5! It is a Streamlit app that uses the PyTrends library to fetch Top and Rising related keyword trends from Google Trends. 
<br>Built by **Orit Mutznik**, fixed by AI. Follow me on **[@OritSiMu on X](https://x.com/OritSiMu)** and **[LinkedIn](https://www.linkedin.com/in/oritsimu/)**.

## App description and functionality

* Paste up to 5 keywords - one per line
* Pick your country (start typing to search) and timeframe
* Hit **Get Trevnds** 🤘
* View Top and Rising related queries for each keyword - up to 25 per list when available
* Export to **CSV** or **XLSX**, or **copy all** to clipboard

**Notes**

* The **value** is not search volume - it is a Google Trends score.
* **Breakout** indicates very high growth.

## Light use

Use the hosted app: **[gtrendalyser2.streamlit.app](https://gtrendalyser2.streamlit.app/)**. The app includes exponential logic to handle temporary rate limits.

> ⚠️ **Important - strategy for heavy users and internal stability**
> This app relies on the unofficial **pytrends** library. Google enforces strict, undisclosed rate limits that can trigger HTTP 429 "too many requests" errors. On shared hosts like Streamlit Community Cloud, heavy usage by others can exhaust the shared IP quota and block everyone.
>
> For stable, uninterrupted use under heavy load, **deploy your own copy** so it runs on a separate resource pool with its own quota.

## Deployment steps for independent stability

1. **Fork the repo** on GitHub.
2. **Create a Streamlit Community Cloud** account and link your GitHub.
3. **Deploy your fork**: New app → select your fork → set the entrypoint to `app.py`.
4. Your personal deployment runs with its own limits - ideal for internal teams and intensive analysis.

## Contact

Questions or feedback? Reach out on **[LinkedIn](https://www.linkedin.com/in/oritsimu/)** or **[@OritSiMu on X](https://x.com/OritSiMu)**. WIP site: **[oritmutznik.com](https://www.oritmutznik.com/)**.

---

<details>
<summary><strong>Why fork and self-host</strong> - optional deep dive</summary>

* Shared IPs can hit 429 rate limits under heavy use
* Your own deploy isolates your quota and avoids noisy neighbors
* You keep control of updates and environment

</details>
