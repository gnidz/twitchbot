# TwitchBot Project

Welcome to the TwitchBot project! This bot is built using the **TwitchIO** library and is designed to enhance your Twitch streaming experience by providing engaging commands, automated responses, and fun interactions for your viewers.

---

## **Features**

1. **Interactive Commands**  
   - `!roulette` - Engage in a thrilling game of Russian Roulette. Alternates between user and target until one loses.
   - `!random` - Randomly selects a winner for giveaways.
   - `!time` - Tracks and displays the total watch time of each user.

2. **Moderation Tools**  
   - Commands to timeout or ban users.
   - User role-based permission checks to ensure security.

3. **Dynamic Category Change**  
   - Use shorthand commands like `!ch just ch` to switch to "Just Chatting" or `!ch valo` for "VALORANT" seamlessly.

4. **Prize System**  
   - Winners of specific commands collect virtual currency stored in a `money.json` file.

5. **Web Integration**  
   - HTML-based wheel randomizer for giveaway entries.

6. **OBS WebSocket Integration**  
   - Automates scene changes and alerts for your stream using the `obs-websocket-py` library.

---

## **Setup**

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/gnidz/twitchbot.git
   cd twitchbot
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Update the `tokens.json` file with the following details:
   ```json
   {
     "TWITCH_TOKEN": "your_twitch_token",
     "TWITCH_CLIENT_ID": "your_client_id",
     "TWITCH_CLIENT_SECRET": "your_client_secret"
   }
   ```

4. **Run the Bot**:
   ```bash
   python bot.py
   ```

---

## **Command Examples**

Here are some command examples and their responses:

### **Game Commands**
- **Command:**
  ```
  !roulette @username
  ```
  **Response:**
  ```
  Bang! You survived this round. Next shot is @username's turn.
  ```

- **Command:**
  ```
  !random
  ```
  **Response:**
  ```
  🎉 Congratulations @username! You've won the giveaway!
  ```

### **Moderation Commands**
- **Command:**
  ```
  !timeout @username 60
  ```
  **Response:**
  ```
  @username has been timed out for 60 seconds.
  ```

### **Category Commands**
- **Command:**
  ```
  !ch valo
  ```
  **Response:**
  ```
  Stream category changed to VALORANT.
  ```
  
---

## **Contact**

For inquiries or support, feel free to reach out via:
- **Email:** tammarathugues@gmail.com
- **Twitch:** [urxi_](https://www.twitch.tv/urxi_)
- **Instagram:** [g.nidz_](https://www.instagram.com/g.nidz_/)

---

Thank you for using the TwitchBot! 🎮

