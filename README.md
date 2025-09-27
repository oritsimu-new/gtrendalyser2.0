# The G-Trendalyser 2.0 🐍🔥

The G-Trendalyser 2.0 is a Streamlit app that uses the PyTrends library to fetch Top and Rising related keyword trends from Google Trends. Built by **Orit Mutznik**. Connect with me on **[@OritSiMu on X](https://x.com/OritSiMu)** and **[LinkedIn](https://www.linkedin.com/in/oritsimu/)**.

## App description and functionality

* Paste up to 5 keywords - one per line
* Pick your country (start typing to search) and timeframe
* Hit **Get Trevnds** 🤘
* View Top and Rising related queries for each keyword - up to 25 per list when available
* Export to **CSV** or **XLSX**, or **copy all** to clipboard

**Notes**

* The **value** is not search volume - it is a Google Trends score.
* **Breakout** indicates very high growth.

## Usage limitations
## Light use

Use the publicly hosted app: **[gtrendalyser2.streamlit.app](https://gtrendalyser2.streamlit.app/)**. The app includes exponential backoff to handle temporary rate limits.

> ⚠️ **Important - strategy for heavy users and internal stability**
> This app relies on the unofficial **pytrends** library. Google enforces strict, undisclosed rate limits that can trigger HTTP 429 errors. On shared hosts like Streamlit Community Cloud, heavy usage by others can exhaust the shared IP quota and block everyone.
>
> For stable, uninterrupted use under heavy load, **deploy your own copy** so it runs on a separate resource pool with its own quota.

## ⚠️More Stable Alternatives

## Deployment steps for independent stability

1. **Fork the repo** on GitHub.
2. **Create a Streamlit Community Cloud** account and link your GitHub.
3. **Deploy your fork**: New app → select your fork → set the entrypoint to `app.py`.
4. Your personal deployment runs with its own limits - ideal for internal teams and intensive analysis.

## Local usage (highest stability)

If you want the absolute highest stability, run the app directly on your machine or an isolated server:

1. **Download** - get the `app.py` and `requirements.txt` files from the repository.
2. **Install** - ensure you have Python installed, then install the required libraries:

```bash
pip install -r requirements.txt
```

3. **Run Streamlit** - navigate to the folder containing `app.py` in your terminal and run:

```bash
streamlit run app.py
```

Your personal deployment runs on a separate resource pool with its own rate limit quota, ensuring maximum stability for heavy analysis and internal teams.

## Contact

Questions or feedback? Reach out on **[LinkedIn](https://www.linkedin.com/in/oritsimu/)** or **[@OritSiMu on X](https://x.com/OritSiMu)**. WIP site: **[oritmutznik.com](https://www.oritmutznik.com/)**.

---

<details>
<summary><strong>Why fork and self-host</strong> - optional deep dive</summary>

* Shared IPs can hit 429 rate limits under heavy use
* Your own deploy isolates your quota and avoids noisy neighbors
* You keep control of updates and environment

</details>
