import cv2
import numpy as np
from insightface.app import FaceAnalysis
import os
import json
import glob
import sys
from datetime import datetime
from rich.console import Console
from rich.progress import Progress

# Initialize rich console for better output
console = Console()

class FaceScanner:
    def __init__(self, embeddings_folder="embeddings", threshold=0.6):
        self.embeddings_folder = embeddings_folder
        self.threshold = threshold
        self.log_file = "scan_log.json"
        
        # Initialize Face Recognition model
        self.app = FaceAnalysis(name="buffalo_l", 
                              providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        
        # Load all embeddings
        self.known_embeddings = self.load_embeddings()

    def load_embeddings(self):
        """Load all embeddings from the embeddings folder"""
        embeddings = []
        metadata_path = os.path.join(self.embeddings_folder, "embeddings_metadata.json")
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            for entry in metadata:
                embedding_path = entry["embedding_path"]
                if os.path.exists(embedding_path):
                    embedding = np.load(embedding_path)
                    embeddings.append({
                        "embedding": embedding,
                        "filename": entry["filename"],
                        "confidence": entry["confidence"]
                    })
        
        return embeddings

    def compare_face(self, face_embedding):
        """Compare face embedding with all stored embeddings and stop at good match"""
        for known in self.known_embeddings:
            similarity = np.dot(known["embedding"], face_embedding)
            if similarity >= self.threshold:
                return True, known, similarity
        
        # If no good match found, find the best match
        best_match = None
        best_similarity = -1
        
        for known in self.known_embeddings:
            similarity = np.dot(known["embedding"], face_embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = known
        
        return False, best_match, best_similarity

    def log_scan_result(self, scan_time, results, image_path):
        """Log scan results to JSON file"""
        log_entry = {
            "timestamp": scan_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "image_path": image_path,
            "faces_detected": len(results),
            "results": []
        }
        
        has_critical_warning = True  # Set to False if any face matches
        
        for result in results:
            result_entry = {
                "is_match": result["is_match"],
                "similarity": result["similarity"],
                "matched_name": result["matched_name"]
            }
            log_entry["results"].append(result_entry)
            
            if result["is_match"]:
                has_critical_warning = False
        
        if has_critical_warning:
            log_entry["critical_warning"] = "No faces matched the known embeddings"
        
        # Load existing log or create new one
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                try:
                    log_data = json.load(f)
                except json.JSONDecodeError:
                    log_data = {"scans": []}
        else:
            log_data = {"scans": []}
        
        # Add new entry and save
        log_data["scans"].append(log_entry)
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)

    def scan_image(self, image_path, save_result=True):
        """Scan an image and compare with known faces"""
        scan_time = datetime.now()
        
        if not os.path.exists(image_path):
            console.print(f"[red][ERROR] Image not found: {image_path}[/red]")
            return None, None
        
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            console.print(f"[red][ERROR] Could not read image: {image_path}[/red]")
            return None, None
        
        # Detect faces
        faces = self.app.get(image)
        results = []
        
        for face in faces:
            # Get face location and embedding
            x1, y1, x2, y2 = map(int, face.bbox)
            is_match, match_info, similarity = self.compare_face(face.normed_embedding)
            
            # Draw results on image
            color = (0, 255, 0) if is_match else (0, 0, 255)
            label = f"Match: {match_info['filename']} ({similarity:.2f})" if is_match else f"Unknown ({similarity:.2f})"
            
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(image, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            results.append({
                "is_match": is_match,
                "similarity": float(similarity),
                "matched_name": match_info["filename"] if is_match else None,
                "bbox": [int(x1), int(y1), int(x2), int(y2)]
            })
        
        # Save annotated image if requested
        if save_result and len(faces) > 0:
            output_path = "scan_result.jpg"
            cv2.imwrite(output_path, image)
        
        # Log the results
        self.log_scan_result(scan_time, results, image_path)
        
        return results, image

def main():
    console.print("[cyan][INFO] Starting face scanning process...[/cyan]")
    
    try:
        scanner = FaceScanner()
        
        # Look for image to scan
        scan_files = glob.glob("for_scan.*")
        
        if not scan_files:
            console.print("[red][ERROR] No image found for scanning. Please place an image named 'for_scan' with .jpg, .jpeg, or .png extension in the project directory.[/red]")
            return
        
        image_path = scan_files[0]
        results, _ = scanner.scan_image(image_path)
        
        # Print results
        console.print("\nScan Results:")
        if not results:
            console.print("[yellow][WARNING] No faces detected in the image.[/yellow]")
        else:
            for i, result in enumerate(results, 1):
                if result["is_match"]:
                    console.print(f"[green][SUCCESS] Face {i}: Match found! Name: {result['matched_name']} (Similarity: {result['similarity']:.2f})[/green]")
                else:
                    console.print(f"[red][WARNING] Face {i}: No match found (Best similarity: {result['similarity']:.2f})[/red]")
        
        console.print("\n[green][INFO] Results saved to 'scan_result.jpg' and 'scan_log.json'[/green]")
        
    except Exception as e:
        console.print(f"\n[red][ERROR] Error during face scanning: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 