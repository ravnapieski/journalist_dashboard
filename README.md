# 🗿 Yle Journalist Dashboard 🗿

Yo, welcome to the absolute GIGACHAD of data projects. This is a dashboard project that scrapes Yle journalist articles, stores the data, and gives you a clean way to explore it. Built to make analysis easy and insights obvious. As Mr. ChatGPT would say it: "no fluff".

We are analyzing who is actually cooking 🍳 and who is just posting Ls.

## 🥶 The Features (Straight Ws)

### 🤖 RAG Chat (The Big Brain) **[NEW]**

We hooked up **Llama (via Groq)** to a local vector database. You can now interrogate the journalist's archives.

- "Summarize the journalist's reportin style." -> **Answered.**
- "Who is missing from their narrative?" -> **Exposed.**
- It cites its sources so no hallucinations, strictly based. 📜

### 🔍 Web Scraping (Selenium + BS4)

The scraper handles Yle’s dynamic content, including “Show More” buttons, and pulls full article text automatically. 🤖

### 🗄️SQLite Database

Storing all the tea ☕. Titles, urls, full body text, keywords. No crumbs left behind. 😤

### 📊Streamlit Dashboard

The frontend is straight moggging like the big Goggins himself🗿 🤫🧏‍♂️

### 🪄 Auto Metadata Detection

Auto-detects the journalist's name and keywords from the HTML meta tags. Big brain energy. 🧠

## 🛠️ The Drip

Python 🐍: The GOAT language.  
Selenium 🕸️: For those suss dynamic pages that try to hide the loot.  
Streamlit 📊: Low code, high rizz.  
SQLite 🗄️: Keeps the data secure, no leaky epstein file vibes.  
LangChain 🦜: The glue holding the galaxy brain together.  
ChromaDB 🌈: Vector store

### 🚀 Quick Start

1.  **Install the Drip:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Secure the Keys 🔑:**
    You need a Groq API key to power the brain.
    - Create a `.env` file in the root folder.
    - Add this line: `GROQ_API_KEY=gsk_your_key_here_...`

3.  **Launch the Dashboard:**

    ```bash
    streamlit run dashboard/app.py
    ```

4.  **The Workflow (How to Flex):**
    - **Search** a Journalist URL -> **Scrape**.
    - Hit the **"🔄 Sync with AI"** button
    - Scroll down to **"AI Assistant"**.
    - Ask: _"Why is this journalist the goat?"_
    - **Profit.** 📈

### 🔮 Future Plans / Already implemented features because the future is now

**Pseudo Stats:** Real analytics aren’t public, so these stats are vibes-only (unless I set up a backdoor while working at Yle 😈😈😈). jk, obviously  
**--> BOOM! MANIFESTED! next up AI hehehe**

**AI / RAG Integration:** We finna hook this up to an LLM so you can chat with the database.
**--> BOOM X2! FINALLY GOT THIS RAG INTEGRATED!!!!! Might still experiment with different prompts and routing or more advanced features later but I'd say this is pretty good for now.**

Status: Kitchen is on fire.🔥🔥🔥 👨‍🍳 Vibes: Immaculate. ✨
