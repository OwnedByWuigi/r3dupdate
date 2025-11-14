<center>
<h1>r3dupdate</h1>
<p>r3dupdate is a r3dfox updater for Windows 7 (and above)</p>
<h2>Scheduled (automatic) updates</h2>
<li>
- Run CreateTask.ps1. This is the file that will create the scheduled task. The scheduled task will run while the current user account is logged on (at start-up and every 4 hours). If you wish to REMOVE the task, run RemoveTask.ps1,
</li>
<br>
<li>
- If your account has administrator permissions, the update will be fully automatic. If not, the update will be downloaded and you will be asked by WinUpdater to start the update (administrator permissions required). 
</li>
<br>
<li>
- If r3dfox is already running, the updater will notify you of the new version. The update will start as soon as you close the browser.
</li>
</center>