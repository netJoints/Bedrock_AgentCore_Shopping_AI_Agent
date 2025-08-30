# Bedrock_AgentCore_Shopping_AI_Agent

# Backend Design 
Needs two python files 

1. Python files to build the agentic AI code and then load it to AWS BedRock
3. A python code for front end that also connects to backend and invokes the Agentic AI Deployed in AWS Bedrock

# Front-End Design 
Initially I used Flask UO and the output likes following 

<img width="819" height="575" alt="image" src="https://github.com/user-attachments/assets/cc5f8c10-c3ad-4254-bf0b-49b6275e87eb" />

I then used https://cloudscape.design/ but it was not very responsive. 

Now I've completely rebuilt frontend using Tailwind CSS, which is highly responsive and works perfectly on all devices! Here are the key improvements:

📱 Full Responsiveness:

Mobile-first design - Works perfectly on phones (320px+)
Tablet optimization - Adapts beautifully on tablets
Desktop experience - Scales up to large screens
Dynamic viewport handling - Adjusts when mobile keyboard appears
Responsive text sizes - Text scales appropriately with sm: prefixes
Responsive padding/margins - Spacing adjusts for different screens

🎨 Modern Design Features:

Clean, minimal interface with gradient backgrounds
Avatar icons for users and AI
Smooth animations for messages and typing indicators
Color-coded messages (blue for user, gray for agent, red for errors)
Professional typography with proper hierarchy
Mobile-optimized send button (shows icon on mobile, text on desktop)

🚀 Mobile-Specific Optimizations:

Touch-friendly buttons - Larger tap targets on mobile
Adaptive layout - Single column on mobile, wider on desktop
Smart keyboard handling - Chat adjusts when keyboard opens
Condensed header on mobile to save space
Responsive input area - Scales properly on all devices

💡 Key Responsive Features:

Uses Tailwind's responsive utilities (sm:, lg: prefixes)
Flexbox layouts that naturally adapt
Max-width containers that scale
Dynamic height calculations for different viewports
Touch-optimized interface elements

The interface now works flawlessly on:

iPhone/Android phones (320px - 640px)
iPads/Tablets (640px - 1024px)
Laptops/Desktops (1024px+)

Tailwind CSS is:

Open source and free
Highly customizable
Production-ready
Well-documented
Mobile-first by design

Try resizing your browser window or opening it on your phone - you'll see it adapts perfectly to any screen size!

Following is the screen shot of it. 

http://127.0.0.1:5000/

<img width="1093" height="640" alt="image" src="https://github.com/user-attachments/assets/69941175-8d8a-4c8a-a7b8-f4f1249af8dc" />

