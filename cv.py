import cv2
import numpy as np

# Circularity filter bounds
circularity_bounds = {"lower": 0.0, "upper": 1.5}

def update_lower_bound(val):
    circularity_bounds["lower"] = val / 100.0

def update_upper_bound(val):
    circularity_bounds["upper"] = val / 100.0

def detect_yellow_ball_real_time():
    # Open a connection to the default camera
    cap = cv2.VideoCapture(0)
    
    # Set resolution (optional)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
    
    # Create a window with trackbars for circularity filter
    cv2.namedWindow("Settings")
    cv2.createTrackbar("Lower Circularity", "Settings", int(circularity_bounds["lower"] * 100), 150, update_lower_bound)
    cv2.createTrackbar("Upper Circularity", "Settings", int(circularity_bounds["upper"] * 100), 150, update_upper_bound)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        # Convert to HSV color space
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define a wider HSV range for yellow
        lower_yellow = np.array([15, 80, 80])  # Adjusted lower bound
        upper_yellow = np.array([35, 255, 255])  # Adjusted upper bound
        
        # Create a mask for yellow
        yellow_mask = cv2.inRange(hsv_frame, lower_yellow, upper_yellow)
        
        # Morphological operations to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_fit = None
        best_score = -1  # Start with an invalid score
        
        for contour in contours:
            # Calculate contour area and perimeter
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * (area / (perimeter ** 2)) if perimeter > 0 else 0
            
            # Filter by circularity and area
            if 500 < area < 5000 and circularity_bounds["lower"] <= circularity <= circularity_bounds["upper"]:
                # Calculate yellowness (mean pixel value in the yellow mask)
                mask = np.zeros_like(cleaned_mask)
                cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
                yellowness = cv2.mean(cleaned_mask, mask=mask)[0]
                
                # Combine circularity and yellowness for scoring
                score = circularity * yellowness
                
                # Update the best fit based on the score
                if score > best_score:
                    best_fit = contour
                    best_score = score
        
        if best_fit is not None:
            # Get the bounding box for the best fit
            x, y, w, h = cv2.boundingRect(best_fit)
            
            # Draw the green bounding box around the best fit
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Write the score and circularity index
            cv2.putText(frame, f"Score: {best_score:.2f}", (x, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, f"Circ: {4 * np.pi * (cv2.contourArea(best_fit) / (cv2.arcLength(best_fit, True) ** 2)):.2f}", 
                        (x, y - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Display the frame with detections
        cv2.imshow("Yellow Ball Detection", frame)
        
        # Display the mask with contours
        contour_display = np.zeros_like(frame)
        cv2.drawContours(contour_display, contours, -1, (255, 255, 255), 1)
        cv2.imshow("Contours", contour_display)
        
        # Exit loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the camera and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

# Run the real-time detection
detect_yellow_ball_real_time()
