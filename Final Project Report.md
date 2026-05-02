# Narra-Tron Project Final Report

## 1. Team Information

- **Team Name:** Storm Brain
- **Team Members:**
  - **Name** ([yourmail@brandeis.edu](mailto:yourmail@brandeis.edu)) – Role
  - Nancy Zhang (huayizhang@brandeis.edu) - Protocol + Camera code
  - Pierce Garbett (piercegarbett@brandeis.edu) - Protocol + Camera code
  - Wenli Cai (wcai@brandeis.edu) - OCR + TTS + 3D Printing
  - Maxwell Weiner (maxweiner@brandeis.edu) - OCR + TTS + 3D Printing
- **Github Repository:**: https://github.com/NancyZhang26/Narra-Tron
- **Demo Link:** https://docs.google.com/presentation/d/1M__KO6UCBetOWG8rkg2rs_iKevis9jkhMCGJpr3hjBI/edit?usp=sharing

## 2. Abstract

Provide a concise summary (150–250 words) describing:

- The problem you are addressing
- Brief description about your proposed project
- Key technologies involved
- Final results and impact

## 3. Project Details

Describe the details about your project

### 3.1 Project Description

High-level description of the system.
As detailed as possible.

### 3.2 Hardware Components

| Component           | Description     | Quantity |
| ------------------- | --------------- | -------- |
| Raspberry Pi pico w | Main controller | 1        |
| Sensor / Module     | Purpose         | X        |
| Power Supply        | Rating          | 1        |

- Schematic

### 3.3 Software Components

- Libraries / Frameworks
- Software structure
  - code structure
- Data flow
- User interface
- Communication Protocols (e.g., I2C, SPI, MQTT)

### 3.4 Overall Control Flow

## 4. Challenges and Limitations

- Technical challenges: debuggin hardware issues when there isn't a specific error message; resolving hardware limitations, such as not enough power to run the OCR+TTS models + camera resolution is too low.
- Design constraints: the hardware problems that we mentioned above. Also, to build a perfect model is hard - the 3D-printed spinner and wheel would need to be able to auto-adjust to different sizes of the book, so we agreed on a minimalistic MVP for a avergae sized, hard cover book.
- What didn’t work as expected: We ran out of time to implement the voice command, but that was a nice-to-have feature, so we let that go. Then, the OCR model was weaker than we expected, so we would need to adjust a higher resolution for the pi camera to give the OCR a better-quality image.
- Potential enhancements: a movable stance for the spinner so it is adjustable to the thickness of the book; even better error handling mechanism achieved by stream of log statements that let us visualize what is the blocker in the entire pipeline; a better UI that can be used in production
- Features you would add with more time: voice comnands to tell the page turner to go forward a page / go back a page; adjustable stance for the spinner that can auto-adjust to the thickness of the book.

## 5. Demo Description

Explain your (recorded) demo:

- How the system works in real time
- Key highlights

## 6. Contributions

List each member’s contributions:

- Nancy: Protocol that transmit HTTP requests and responses between the speaker (pi), page turner hardware (3-D printed) (pico), camera (pi). Camera preview + Camera code.
- Pierce:
- Wenli:
- Max:

## 7.Conclusion

Summarize:

- What you built
- What you learned: **_Software efficiency is inevitably tied with hardware limitations._**
- Overall success of the project: Got a working MVP. Yeppie!

## References

- Datasheets
- Research papers
- Projects you get ideas from - GitHub repositories
