# Module 1 Group Assignment

CSCI 5117, Fall 2026, [assignment description](https://canvas.umn.edu/courses/579310/pages/project-1)

## App Info:

* Team Name: Brain Underflow
* App Name: Tune In
* App Link: https://developing-the-interactive-web-project-1-mde9.onrender.com

### Students

* Mohith Siva Sai Bayana, bayan009@umn.edu
* Jyothsna Mysore Santhosh Kumar, ms000001@umn.edu
* Ashmitha Ashokkumar, ashok058@umn.edu
* Hui Qin Rochelle Kwang, kwang008@umn.edu


## Key Features

* Discover music performances with search, genre filters, trending videos and artists, and personalized video recommendations.
* Watch videos and interact through likes and threaded comments, including replies, editing, deletion, and comment likes.
* Subscribe to creators and organize videos into custom playlists, Saved Videos, and a Watch Later list.
* Upload videos and thumbnails, save drafts, publish videos, and edit or delete uploads in Creator Studio.

## Testing Notes

* Sign-in and sign-up use Auth0. Testing account-only features requires signing in and completing profile setup.
* The app requires a configured PostgreSQL database and Cloudflare R2 bucket; upload, thumbnail, and playback workflows rely on R2.
* Test the logged-out experience, then sign in to try search and genre browsing, video playback, likes/comments, subscriptions, playlists, and creator upload/manage features.


## Screenshots of Site

![Tune In home page](images/home_page_ss.png)
*Discover videos from the signed-in home page.*

![Trending page](images/trending_ss.png)
*Browse trending videos, artists, and genres.*

![Library page](images/library_ss.png)
*Find playlists, saved videos, and Watch Later.*

![Video player](images/mediaplayer_ss.png)
*Watch a performance and join the conversation.*


## Mock-up 

### 1. Logged-out Landing page
![Logged-out Landing page](images/logge-out-home.jpeg)

This is the Landing page of our application when the user is logged-out. Some of the functionalities of the application will be missing.

### 2. Login page
![Login page](images/login.jpeg)

This is the pop window when the user clicks on the login buttion.

### 3. sign-up page
![sign-up page](images/sign_up.jpeg)

This is the pop-up window when the user hits the sign-up button

### 4. Logged-in Landing page
![Logged-in landing page](images/IMG_2298.jpeg)

This is the landing page when the user is logged-in.

### 5. Trending page
![Trending page](images/IMG_2299.jpeg)
This is the trending page where user can find trending songs/artists/genres.

### 6. Subscriptions page
![Subscriptions page](images/IMG_2300.jpeg)
This is the subscriptions page where user can find the artists they subscribed to.

### 7. Library page
![Library page](images/IMG_2301.jpeg)
This is the Library page where user can find their playlists, saved videos and videos to watch later.

### 8. Activity page
![Activity page](images/IMG_2302.jpeg)
This is the Activity page where user can find their liked videos and their comments om different videos.

### 9. Upload page
![Upload page](images/IMG_2303.jpeg)
This is page where users upload their videos

### 10. Upload page pop-up
![Upload page pop-up](images/new_video.jpeg)
This is a pop-up window when the user clicks on the '+' button on the upload page

### 11. Manage Videos Page
![profile](images/ManageVideosFinal.PNG)
This is the Manage Videos page where users can see and manage all the videos they have posted. Upon clicking the three dots, the option to either Edit or Delete each video appears via a pop-up menu that is overlaid on the video

### 12. Edit Video
![profile](images/IMG_2310.PNG)
This is the Edit Video popup that shows up when Edit is selected from the pop-up menu mentioned on 11. The video creator has the option to edit the title and description of the video, as well as upload a new thumbnail for the video.

### 13. Delete Video Confirmation Popup
![profile](images/IMG_2316.PNG)
This is the popup that verifies that the user would like to proceed with deleting the video.

### 14. Profile page
![profile](images/IMG_2306.jpeg)
This is the profile page when the user clicks on their/other user's profile

### 15. Account Settings page
![settings](images/IMG_2307.jpeg)
On the account settings page, users have access to make modifications to their profile

### 16. Edit Profile Picture
![edit_pp](images/edit_pp.jpeg)
Users can edit their profile picture (add or remove) on this page

### 17. Edit Account Info
![edit_info](images/Acc_info.jpeg)
Users can update their account info including their username, phone and email via this page

### 18. Edit Password
![edit_pswd](images/edit_psswd.jpeg)
Users can change their passwords through this pop window

### 19. Edit Bio
![edit_bio](images/edit_bio.jpeg)
Users can update their bio and save the changes on this pop up window

### 20. Video Player
![vid-player](images/Video_Player.JPG)
This is the media player window. Users can view the videos on this page. They can like, share, subscribe and view, add, edit their comments, with comment editing and deleting down by pressing the three dots.

### 21. Delete Comment Pop-up
![vid-menu](images/IMG_2315.PNG)
Clicking on the delete option of the three dots on the comments opens up a window seeking delete confirmation.

### 22. Menu Pop-up on video Player
![vid-menu](images/video_menu.jpeg)
The three dots on the media player area leads to this dropdown options. They can save videos and add to watch later. They can also create and save to existing playlists

## External Dependencies

**Document integrations with 3rd Party code or services here.
Please do not document required libraries. or libraries that are mentioned in the product requirements**

* **Auth0:** Provides user sign-up and sign-in; the application uses Auth0 credentials to associate authenticated accounts with Tune In profiles.
* **Cloudflare R2:** Stores uploaded videos, video thumbnails, and profile pictures, which the app retrieves for playback and display.
* **PostgreSQL:** Stores application data, including user profiles, videos, comments, subscriptions, and playlists.

**If there's anything else you would like to disclose about how your project
relied on external code, expertise, or anything else, please disclose that
here:**

We asked our friends who are into music to send in their music videos for our website
