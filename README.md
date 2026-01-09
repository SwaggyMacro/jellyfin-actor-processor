# jellyfin-actor-processor
This is a simple script that will refresh the actors from the Jellyfin API.
I made this to fix the issue where the actor's image are not showing up in the Jellyfin until you click the actor to view the actor's detail page or delete the actor image once.

This script is inspired by a PowerShell script developed by [nagug](https://github.com/nagug/Jellyfin-Actor-Refresh-Script), designed to tackle specific problems such as the Jellyfin actor refresh issue. This problem, where Jellyfin occasionally struggles to update actor information correctly, has been discussed in the Jellyfin thread: [jellyfin/jellyfin#8103](https://github.com/jellyfin/jellyfin/issues/8103).

> **nagug**: While working with the script, it was discovered that this method also helps resolve a separate issue with Infuse:  
> - Infuse Actor Display Issue: Infuse may not display actors correctly if actor details are present in .nfo files. This script helps mitigate this issue by refreshing the actor metadata in Jellyfin, which in turn can improve actor display in Infuse.
# How to use
1. Clone this repository
2. Run `python main.py -url <Jellyfin URL> -key <Jellyfin API Key>`

# Example
`python main.py -url http://localhost:8096 -key 1234567890abcdef1234567890abcdef`
![image](https://github.com/user-attachments/assets/dd344991-a811-41cb-ae4d-79eba4c28a08)

# Options
```shell
$python .\main.py --help

usage: main.py [-h] -url URL -key API_KEY [-f] [-r RETRIES] [-w WORKERS] [-t TIMEOUT]

Jellyfin Actor Processor

options:
  -h, --help            show this help message and exit
  -url URL, --url URL   Jellyfin server URL
  -key API_KEY, --api-key API_KEY
                        Jellyfin API key
  -f, --force           Process all persons
  -r RETRIES, --retries RETRIES
                        Maximum number of retries for failed requests
  -w WORKERS, --workers WORKERS
                        Maximum number of parallel workers
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout in seconds for fetching person data (default: 30)
```
# Features
- Refreshes actor metadata: Automates API calls to Jellyfin to update actor information.
- Helps resolve Infuse display issue: Mitigates the issue of Infuse not showing actors correctly when details are in .nfo files.
- Force flag: Allows processing of all actors, regardless of their image tag status, using the --force flag.
- Server ping check: Verifies if the Jellyfin server is reachable.
- Error handling: Includes error handling for API calls and server availability.
- Progress bar: Displays a progress bar to visually track the refresh process.
- Informative output: Provides clear and colorful output with status messages and error reporting.

# Screenshots
## Before
![9332cebedaf073e59e09bd739195351](https://github.com/user-attachments/assets/f2c9777c-0ba9-486d-af4e-4e4ef6f294f4)
![d5802d6ce8340f9aa0633ba243a18bb](https://github.com/user-attachments/assets/33cdd647-14d9-4652-98e4-1fe92eb92a89)
![6d22981ab0e7258f92ce4411df1db58](https://github.com/user-attachments/assets/227100bf-495d-4fc3-883f-cd218eb066d5)
## After
![image](https://github.com/user-attachments/assets/527400d0-12fb-4376-819f-802304912add)
![image](https://github.com/user-attachments/assets/32f30007-deb8-428b-99d8-cb06ea028894)
![image](https://github.com/user-attachments/assets/1c0778bf-f938-4d8a-9c5a-8418ad9a1532)
