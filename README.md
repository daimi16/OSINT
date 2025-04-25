# ITMS-448/548 OSINT Project

An OSINT gathering application written in Python for the course ITMS 448/548:

According to the requirements we have included 4 API's in the sources.
The 4 API's utilised were : News API, Reddit API, data.gov API, and Aviation Stack's API.



## Requirements and Dependencies

- Python 3.7+
- Libraries required are listed in the requirements.txt

## Steps for using the project

1. Using git commands clone the repository:
   ```
   git clone https://github.com/daimi16/OSINT.git
   cd OSINT
   ```

2. Install the dependencies, ensure there are no errors here, otherwise the project will not function:
   ```
   pip install -r requirements.txt
   ```

3. Replace the placeholders in config.py with actual API keys from the required websites, for our privacy we have removed the keys from the files pushed to github.


4. While inside the directory with all the project files, run this command to launch the project:
   ```
   python app.py
   ```
