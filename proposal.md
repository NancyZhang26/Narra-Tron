# Narra-Tron - Proposal




## 1. Team Information
- **Team Name:** Storm Brain
- **Team Members:**
  - **Maxwell Weiner** ([maxweiner@brandeis.edu](mailto:maxwell@brandeis.edu)) – Role
  - **Pierce Garbett** ([piercegarbett@brandeis.edu](mailto:piercegarbett@brandeis.edu)) – Role
  - **Wenli Cai** ([wcai@brandeis.edu](mailto:wcai@brandeis.edu)) – Role  
  - **Nancy Zhang** ([huayizhang@brandeis.edu](mailto:huayizhang@brandeis.edu)) – Role




- **Github Repository:** [Github Repo Link](https://github.com/NancyZhang26/AI-Page-Reader-Turner)




## 2. Abstract
Our project, Narra-Tron, is an AI reading tool that takes any physical book and turns it into an e-book. Not only are more and more people favoring audio content – such as podcasts and e-books - over video content, but everyone is getting busier. We want everyone to still be able to consume their favorite media during commutes, meals, and errands. But you aren’t able to find every book online. So, we’re coming up with a way to take any book you own and transform it into audio content. This will be a two-part project, one that involves transcribing pictures taken by a camera into audio, and another that automatically flips each page before the camera takes another snapshot of the pages. We expect that the first part will mostly be software-based, while the second part will be focused on hardware tuning to make the page-turning mechanism precise. In the end, we will allow books to be inserted into the cradle, and by starting the machine, users will immediately be able to hear the book they want to read.


## 3. Objectives
The main objectives of this project are:
List the specific goals of the project

- Import a text-to-speech library that can convert text to audio speech signals
- Connect the library with a camera that can convert a physical page into an image of texts
- Make a hardware that is able to turn a page of a general book
- Connect all pieces together and make a protocol to let the software talk to the hardware and collaborate in a relatively smooth, accurate way.




## 4. Proposed Solution


### 4.1 Project Description
Narra-Tron as a whole will have multiple different pieces of software and hardware to help it fully function. 
In terms of software, we will be utilizing both Text2Speech and Speech2Text, as well as protocols to help different software components talk to each other. Text2Speech will be used for our robot to read out the words from the input book as it receives them. Speech2Text, on the other hand, will be for the user to give the robot voice commands, such as “Start”, “Stop”, and “Back”, to enhance their audio reading experience. The protocols will allow each component to understand each other’s progress. (e.g. When the speaker finishes narrating one full page, the protocol will send a signal to the page turner’s hardware to turn the page).
For hardware, the main component of Narra-Tron is the ability to turn pages. We will do this using our own 3D-printed finger and roller. The roller will function as an arm to move the finger to the edge of the pages while the finger performs the flipping. We will need to add a camera and speaker to scan the texts inside the book into an online database for our robot to then read out loud. Finally, we will be using a microphone to take in the user’s voice for the vocal commands.


### 4.2 Hardware Components
| Component | Description | Quantity |
|---------|-------------|----------|
| Raspberry Pi Pico | Main controller | 1 |
| Page turner | A 3-D printed roller and pointer that can turn one page of a general book | 1 |
| Power Supply | Supply the page turner, camera, and Raspberry Pi Pico | 1 |
| Camera | For scanning text | 1 |
| Speaker | To read out the text | 1 |
| Microphone | For advanced voice control | 1 |


- Schematic


Once the text2speech finishes reading the current page, whether that’s in a while loop or by analyzing the text/audio file we produce, then we immediately trigger the physical device to turn the page. 


### 4.3 Software Components
- Libraries / Frameworks


We plan to use [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) for speech-to-text. Full-size Whisper won’t be able to run locally on the Raspberry Pi, but Faster-Whisper is quantized, and the Pi should be able to handle near real-time speech-to-text with ‘’’tiny’’’ or ‘’’base’’’ models.

For fast local text-to-speech generation, we will use [Piper](https://github.com/OHF-Voice/piper1-gpl).

For parsing book page scans, we will use PaddleOCR.


Running all of these models at once may be too resource-intensive for the Raspberry Pi. During the development process, we will need to evaluate how well each component runs locally. If necessary, we can move to a cloud-based solution, which will give us the option to use more powerful models.


- Communication Protocols (e.g., I2C, SPI, MQTT)


For the camera, we will use the built-in Raspberry Pi camera connector and drivers. To drive the DC motors for the page roller and finger, we will use Pulse Width Modulation (PWM). For our microphone and speakers, we will use USB drivers from the manufacturer.


- Software architecture

```Hardware Controller```
	- Turn pages.
	- Get page images from the camera.
	- Play audio on the speaker.
	- Get audio from the microphone.

```OCR Service```
	- Parse text from page images.
	- Output text in a structure that can be used by a TTS engine.

```TTS Service```
	- Generate audio from text.
  
```STT Service```
	- Parse audio into system function calls such as start(), turn_page(), go_back() etc.




- Data flow


Input: (book) -> camera -> raw image data

Processing: raw image data -> `PaddleOCR` -> text

Output: text -> `Piper` -> audio

Overarching control: text2speech -> page-turner

Interrupt sequence: audio commands -> `Fast-Whisper` -> pauses reading and page turner to execute new command


- User interface
	
At the bare minimum, the user will just be able to turn on the device, and the camera + page-turner will immediately start. We aim to incorporate a microphone into the device so it can use audio commands as well. This will simplify the user experience to only require them to insert the book, then say simple commands, like “Start”, “Stop”, “Turn”, and “Back” For advanced control and management of saved audio files, a web app is available and hosted locally on the Pi.




## 5. Methodology
Explain how the project will be developed:
#### Requirement analysis


We will research many libraries for the various aspects of page turning, and explore various options. But we are also open to changing them down the line, based on size of libraries and usability. We will also figure out the different ways for the physical components to be seamless, but that will require trial-and-error. Since we have a reference, we expect to follow broadly along the idea presented in the video, then make microadjustments as needed, detailed below in Hardware Setup.
  
#### Hardware setup
Each page is turned with a roller to lift the page. A mechanical finger reaches under the gap and pushes the page to the opposite side. The roller is weighted so that as the remaining pages decrease, the wheel remains in contact with the page. We will be 3D printing a stand/Pi 5 + Pico case that conceals our wires and elevates the camera above the pages. The Pico will be connected to the Pi 5 via micro-USB cable. The speaker and microphone will be connected to the Pi 5 via USB. Our motors will connect to the Pico with _Grove Shield for Pico_ and included cables.


#### Software development


Since we do not have prior experience working with these libraries, we anticipate using some time to learn how to use these libraries effectively for our text. But since the camera is only trying to read simple text, we do not anticipate that the models will have a hard time (as opposed to something like hand written text)


#### Integration and testing  


The major integration step will be connecting the page-reader to the page-turner. We need the turning to happen seamlessly after the audio works. Because there are physical components to turning the page, we can only manually test that the page turning is successful 100% of the time. This could be done with an automated loop to just let it run. If we assume that the page turning is successful, then the software can just test the trigger of the DC Motor as the bridge from software to hardware. 


When testing the page turning mechanism, it is likely that some pages will be ripped, and books destroyed. To minimize cost, we will use blank notebooks. Using notebooks of different sizes and page thicknesses will prepare us to use various types of books in our final product.


#### Deployment 


Aligning with the future goals of having a web app and (if needed) having a cloud solution for hosting the models, we will be able to deploy both a website for holding previously read books as well as servers for the larger library models.




## 6. Timeline
As detailed as possible.
| Phase | Activities | Duration |
|------|------------|----------|
| Phase 1 | Research & Planning | 1 week |
| Phase 2 | Software Development (Text to speech) | 2 weeks |
| Phase 3 | Hardware Development (Page turner) | 2 weeks |
| Phase 4 | Testing | 1 weeks |
| Phase 5 | Final Deployment + Edits | 1weeks |


## 7. Expected Outcomes


We expect to have our finished 3D printed prototype able to take a physical book and read out the pages through Text2Speech. The prototype should also be able to take certain voice commands from the user to start, stop, return to the previous page, and others we might think of along the way. We would like to maintain a 100% accuracy on the words we read as well as a quick response time for the voice commands. Our project will be very useful for users with little time to sit down and read, as well as users with ADHD who don’t want to sit down and read a book.


## 8. Conclusion


The Narra-Tron project bridges the gap between physical books and digital accessibility. By merging software and hardware, we aim to create a vital tool for those with visual impairments, physical disabilities, or neurodivergent needs.


Our project is technically feasible through various efficient models to allow for ML libraries to be used on low-power hardware. While the mechanical page-turning mechanism presents a complex challenge, our testing approaches ensure a robust, physical solution.


Using Narra-Tron will be a seamless experience that helps us to reclaim our independence and productivity in an increasingly busy world.


## References
- [Piper](https://github.com/OHF-Voice/piper1-gpl)
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 
- [Page turner mechanism](https://www.youtube.com/watch?v=WpUmWCApFB4&pp=ygUpM2QgcHJpbnRlZCBhdXRvIHBhZ2UgdHVybmVyIHdlYXJlcHJpbnRsYWI%3D)  
