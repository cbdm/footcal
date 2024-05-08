# footcal 

This is a webapp to serve the upcoming soccer schedule for your favorite team or competition as an ics calendar.

Live at [footcal.cbdm.app](https://footcal.cbdm.app) and you can check the service status at [status.cbdm.app](https://status.cbdm.app/)  
If you need help using it, check the help page in [footcal.cbdm.app/help](https://footcal.cbdm.app/help)

## How to use
1. Select a team that you want a calendar
2. Get your calendar in iCalendar format
3. Input calendar URL into preferred app (e.g., Google Calendar)

## Contributions welcome
Take a look at the [issues page](https://github.com/cbdm/footcal/issues) for contribution ideas. But please feel free to contribute new ideas too!  
How to contribute:
1. Fork this repository
2. Clone the fork 
3. Make changes and commit them
4. Push your changes
5. Create a pull request

Please reach out if you need help or have questions.

## Running it locally
1. Clone this repo
2. Install [docker](https://docs.docker.com/get-docker/)
3. Navigate into the `testdb` folder and run `docker-compose up` -- this will setup a simple database with some data for you to use
4. Install the requirements with `pip3 -r requirements.txt`
5. Get a key for the [api-sports](https://api-sports.io/) service and update it in the `auth.py` script by either (i) creating the appropriate env variable (preferred!) or (ii) replacing the `XxXx...` with your own key. If you go with (ii), please do NOT commit/push your key!
6. Run the `app.py` script with `python3 footcal/app.py`
7. You should be able to access the app in `localhost:5000`, and the database in `localhost:40001`

Note that step 5 might not be needed if you're not trying to do something with fetching/updating data, as we only talk to api-sports to update local information. If you don't need that, you can use the sample data (step 3) and either live with the errors or change the `cache.py:query` method to never return None.
