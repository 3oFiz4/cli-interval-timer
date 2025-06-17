# cli-interval-timer
A simple Command Line interval timer. Made it in like a hour. I made it this to help me with my meditaiton, because sometimes I only brought laptop. Lol.
---
![cmd_BRNOiYN3EH](https://github.com/user-attachments/assets/eba68322-4351-4580-8d8c-0b9e113ceb38)
---
## How to Use
I didn't provide the guide in the command (my bad). So here's how:
```
timer 1h20m'X'[bowl] // This will create a timer called 'X', of 1 hour and 20 minute, with alarm of 'bowl' in `ringtone/`

timer 1h20m'X'[bowl]; 5m'Y'[bell] // This will do exacty like above, EXCEPT, after it ends, it will run another timer called 'Y', of 5 minutes, with alarm of 'bell' in `ringtone/`

timer --save-template "test" 1h20m'X'[bowl] // Saved the current timer interval as "Test" in `template.json`

timer -l // List the whole saved template

timer {template_name} // Run a saved timer with template_name. For test, you can try run `timer {meditation_hour}` instead.

<Ctrl + C> + Y/N // To initiate process termination reuest, Y=yes, N=no

<W> // To pause

<Q> // Force quit

```
# Requirements
`rich playsound keyboard asyncio`
---
## Set
### Fresh Start
1. On your terminal, run `python timer.py  1m20s'TEST' [bowl]` for example
   
### By PATH, meaning you can use it in any directory (recommended)
Make sure you installed the requirements already

1. Clone this repo to your `C:/Users/[your-name]` as `bin` (I assume you know how)
2. Go to `Computer`, right shift and click `Property`, go to `Advanced`, and `Click` Environmental Variables
3. On `System Variables`, choose Path and click `Edit`
4. Click `New`, and add this `C:\Users\[your-name]\bin\`
5. Click `Ok`, and `Ok`, and `Ok`
6. On your Command Line, run `timer 1m20s'TEST' [bowl]` (will run a 1 minute 20 second timer labelled TEST with alarm of bowl in `ringtone/`
---
