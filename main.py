import cv2 as cv

global model_path
             
if __name__ == "__main__":
    import config
    user_input = ""
    
    while True:
        
        if(user_input in ["image", "video", "stream"]):
            print("Hello!")
            break
        else:
            user_input = input("What would you like to process today?(Image/Video/Stream)")
            user_input.lower()
    
    if(config.model_path == ""):
        config.model_path = input("What is the path of your model?: ")
    
    
    match user_input:
                
        case "image":
            config.image_path = input("What is the path to your image? ")
            import processing.image_landmarks as image_landmarks
            image_landmarks.run()     
        case "video":
            try:
                config.video_path = input("What is the path to your video?: ")
                import processing.video_landmark as video_landmark        
                video_landmark.run()
            except Exception as e:
                print(f"An error has occurred: {e}")
                      
        case "stream":
            
            record = input("Would you like to record this stream?(y/n): ")
            import processing.livestream_landmarks as livestream_landmarks    
            if(record.strip().lower() == "y"):
                if(not config.remember):
                    config.annotated_livestream_path = input("Where would you like to save this stream?: ")
                remember_answer = input("Do you always want to save to this location?(y/n)")
                config.remember = remember_answer.strip().lower()
                livestream_landmarks.run(True) 
            else:
                livestream_landmarks.run(False)
                
            