import sys
import os
import platform
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DaVinciAPI')

# Setup environment variables for DaVinci Resolve
def setup_resolve_env():
    """Configure environment variables based on the operating system."""
    logger.info(f"Setting up DaVinci Resolve environment for {platform.system()} ({sys.platform})")
    
    # Check Python architecture - DaVinci Resolve requires 64-bit Python
    is_64bit = sys.maxsize > 2**32
    logger.info(f"Python architecture: {'64-bit' if is_64bit else '32-bit'}")
    if not is_64bit:
        logger.error("DaVinci Resolve requires 64-bit Python")
        raise RuntimeError("DaVinci Resolve requires 64-bit Python")
    
    # Set direct paths based on platform - similar to working script
    if sys.platform.startswith("darwin"):  # macOS
        resolve_script_api = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
        resolve_script_lib = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
        
        # Check for Studio version if standard version not found
        if not os.path.exists(resolve_script_lib):
            resolve_script_lib = "/Applications/DaVinci Resolve Studio/DaVinci Resolve Studio.app/Contents/Libraries/Fusion/fusionscript.so"
            
    elif sys.platform.startswith("win"):  # Windows
        resolve_script_api = os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), 
                                         "Blackmagic Design", "DaVinci Resolve", "Support", 
                                         "Developer", "Scripting")
        resolve_script_lib = os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), 
                                         "Blackmagic Design", "DaVinci Resolve", "fusionscript.dll")
        
        # Check x86 path if standard path not found
        if not os.path.exists(resolve_script_lib):
            resolve_script_lib = os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), 
                                             "Blackmagic Design", "DaVinci Resolve", "fusionscript.dll")
            
    elif sys.platform.startswith("linux"):  # Linux
        resolve_script_api = "/opt/resolve/Developer/Scripting"
        resolve_script_lib = "/opt/resolve/libs/Fusion/fusionscript.so"
        
        # Alternative Linux paths
        if not os.path.exists(resolve_script_api):
            resolve_script_api = "/home/resolve/Developer/Scripting"
            
        if not os.path.exists(resolve_script_lib):
            resolve_script_lib = "/home/resolve/libs/Fusion/fusionscript.so"
    else:
        logger.error(f"Unsupported operating system: {sys.platform}")
        raise OSError(f"Unsupported operating system: {sys.platform}")
    
    # Verify paths exist
    if not os.path.exists(resolve_script_api):
        logger.error(f"DaVinci Resolve API path does not exist: {resolve_script_api}")
        raise FileNotFoundError(f"DaVinci Resolve API path not found: {resolve_script_api}")
        
    if not os.path.exists(resolve_script_lib):
        logger.error(f"DaVinci Resolve library path does not exist: {resolve_script_lib}")
        raise FileNotFoundError(f"DaVinci Resolve library path not found: {resolve_script_lib}")
    
    # Set environment variables
    os.environ["RESOLVE_SCRIPT_API"] = resolve_script_api
    os.environ["RESOLVE_SCRIPT_LIB"] = resolve_script_lib
    
    # Add to Python path - Using sys.path.append directly instead of modifying PYTHONPATH
    modules_path = os.path.join(resolve_script_api, "Modules")
    if not os.path.isdir(modules_path):
        logger.error(f"Resolve scripting modules path does not exist: {modules_path}")
        raise FileNotFoundError(f"Resolve scripting modules path not found: {modules_path}")
        
    logger.info(f"Adding to Python path: {modules_path}")
    sys.path.append(modules_path)
    
    # Log current environment for debugging
    logger.info(f"RESOLVE_SCRIPT_API set to: {os.environ.get('RESOLVE_SCRIPT_API')}")
    logger.info(f"RESOLVE_SCRIPT_LIB set to: {os.environ.get('RESOLVE_SCRIPT_LIB')}")
    logger.info(f"Added {modules_path} to sys.path")
    
    return resolve_script_api, modules_path

# Try to import DaVinciResolveScript after environment setup
def import_resolve_script():
    """Import the DaVinciResolveScript module after environment setup."""
    try:
        logger.info("Attempting to import DaVinciResolveScript...")
        import DaVinciResolveScript as dvrs
        logger.info("Successfully imported DaVinciResolveScript")
        return dvrs
    except ImportError as e:
        logger.error(f"ImportError: {str(e)}")
        logger.error(traceback.format_exc())
        # Search Python path for the module
        logger.info("Checking Python path for DaVinciResolveScript module:")
        for path in sys.path:
            if os.path.exists(path):
                logger.info(f"  - {path} (exists)")
                # Check if the module exists in this path
                if os.path.exists(os.path.join(path, "DaVinciResolveScript.py")):
                    logger.info(f"    Found DaVinciResolveScript.py in {path}")
            else:
                logger.info(f"  - {path} (does not exist)")
        return None
    except Exception as e:
        logger.error(f"Unexpected error importing DaVinciResolveScript: {str(e)}")
        logger.error(traceback.format_exc())
        return None

class DaVinciResolveAPI:
    def __init__(self):
        """Initialize connection to the actual DaVinci Resolve API."""
        self.resolve = None
        try:
            logger.info("Setting up DaVinci Resolve environment...")
            setup_resolve_env()
            
            logger.info("Importing DaVinciResolveScript...")
            dvr_script = import_resolve_script()
            if not dvr_script:
                logger.error("Could not find DaVinciResolveScript module")
                raise ImportError("Could not find DaVinciResolveScript module. Make sure DaVinci Resolve is installed and running, and scripting is enabled in preferences.")
            
            logger.info("Connecting to DaVinci Resolve application...")
            self.resolve = dvr_script.scriptapp("Resolve")
            if not self.resolve:
                logger.error("Unable to connect to DaVinci Resolve application")
                raise ConnectionError("Unable to connect to DaVinci Resolve. Make sure it's running and that scripting is enabled in preferences.")
            
            logger.info("Successfully connected to DaVinci Resolve")
        except ImportError as e:
            logger.error(f"ImportError: {str(e)}")
            raise ImportError(str(e))
        except Exception as e:
            logger.error(f"Error connecting to DaVinci Resolve: {str(e)}")
            logger.error(traceback.format_exc())
            raise ConnectionError(f"Error connecting to DaVinci Resolve: {str(e)}")

    def is_resolve_running(self):
        """Check if DaVinci Resolve is running and accessible."""
        try:
            if self.resolve:
                version = self.resolve.GetVersionString()
                logger.info(f"DaVinci Resolve is running, version: {version}")
                return {"status": True, "version": version}
            logger.error("Could not connect to DaVinci Resolve")
            return {"status": False, "error": "Could not connect to DaVinci Resolve"}
        except Exception as e:
            logger.error(f"Error checking if Resolve is running: {str(e)}")
            return {"status": False, "error": str(e)}

    def get_basic_project_info(self):
        """Get just the basic project information requested.
        
        Returns:
            dict: Contains project name, framerate, and timeline count
        """
        try:
            logger.info("Getting project manager...")
            project_manager = self.resolve.GetProjectManager()
            
            logger.info("Getting current project...")
            current_project = project_manager.GetCurrentProject()
            
            if not current_project:
                logger.warning("No project is currently open")
                return {"error": "No project is currently open"}
            
            # Get only the requested basic project information
            project_name = current_project.GetName()
            framerate = current_project.GetSetting("timelineFrameRate")
            timeline_count = current_project.GetTimelineCount()
            
            logger.info(f"Project info retrieved: {project_name}, framerate: {framerate}, timeline count: {timeline_count}")
            
            project_info = {
                "name": project_name,
                "framerate": framerate,
                "timeline_count": timeline_count
            }
            
            return project_info
        
        except Exception as e:
            logger.error(f"Error getting project info: {str(e)}")
            return {"error": f"Error getting project info: {str(e)}"}

    def get_timeline_info(self):
        """Get current timeline information.
        
        Returns:
            dict: Contains timeline details like name, frames, timecode and track counts
        """
        try:
            logger.info("Getting project manager...")
            project_manager = self.resolve.GetProjectManager()
            
            logger.info("Getting current project...")
            current_project = project_manager.GetCurrentProject()
            
            if not current_project:
                logger.warning("No project is currently open")
                return {"error": "No project is currently open"}
            
            logger.info("Getting current timeline...")
            current_timeline = current_project.GetCurrentTimeline()
            
            if not current_timeline:
                logger.warning("No timeline is currently open")
                return {"error": "No timeline is currently open"}
            
            # Get timeline information
            name = current_timeline.GetName()
            start_frame = current_timeline.GetStartFrame()
            end_frame = current_timeline.GetEndFrame()
            start_timecode = current_timeline.GetStartTimecode()
            
            # Get current timecode (when available)
            try:
                current_timecode = current_timeline.GetCurrentTimecode()
            except:
                current_timecode = None
            
            # Get track counts
            video_track_count = current_timeline.GetTrackCount("video")
            audio_track_count = current_timeline.GetTrackCount("audio")
            subtitle_track_count = current_timeline.GetTrackCount("subtitle")
            
            logger.info(f"Timeline info retrieved: {name}, frames: {start_frame}-{end_frame}, tracks: V{video_track_count}/A{audio_track_count}/S{subtitle_track_count}")
            
            timeline_info = {
                "name": name,
                "start_frame": start_frame,
                "end_frame": end_frame,
                "start_timecode": start_timecode,
                "current_timecode": current_timecode,
                "track_count": {
                    "video": video_track_count,
                    "audio": audio_track_count,
                    "subtitle": subtitle_track_count
                }
            }
            
            return timeline_info
        
        except Exception as e:
            logger.error(f"Error getting timeline info: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": f"Error getting timeline info: {str(e)}"}

    def get_media_pool_info(self):
        """Get information about the current media pool.
        
        Returns:
            dict: Contains media pool information like current folder and selected clips
        """
        try:
            logger.info("Getting project manager...")
            project_manager = self.resolve.GetProjectManager()
            
            logger.info("Getting current project...")
            current_project = project_manager.GetCurrentProject()
            
            if not current_project:
                logger.warning("No project is currently open")
                return {"error": "No project is currently open"}
            
            logger.info("Getting media pool...")
            media_pool = current_project.GetMediaPool()
            
            if not media_pool:
                logger.warning("Could not access media pool")
                return {"error": "Could not access media pool"}
            
            # Get media pool information
            root_folder = media_pool.GetRootFolder()
            current_folder = media_pool.GetCurrentFolder()
            selected_clips = media_pool.GetSelectedClips()
            
            root_folder_name = root_folder.GetName() if root_folder else "Unknown"
            current_folder_name = current_folder.GetName() if current_folder else "Unknown"
            selected_clips_count = len(selected_clips) if selected_clips else 0
            
            logger.info(f"Media pool info retrieved: Current folder: {current_folder_name}, Selected clips: {selected_clips_count}")
            
            media_pool_info = {
                "root_folder": root_folder_name,
                "current_folder": current_folder_name,
                "selected_clips": selected_clips_count
            }
            
            return media_pool_info
        
        except Exception as e:
            logger.error(f"Error getting media pool info: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": f"Error getting media pool info: {str(e)}"}

    def get_render_jobs(self):
        """Get information about render jobs.
        
        Returns:
            dict: Contains render job information like count and details of each job
        """
        try:
            logger.info("Getting project manager...")
            project_manager = self.resolve.GetProjectManager()
            
            logger.info("Getting current project...")
            current_project = project_manager.GetCurrentProject()
            
            if not current_project:
                logger.warning("No project is currently open")
                return {"error": "No project is currently open"}
            
            # Get render jobs list
            job_list = current_project.GetRenderJobList()
            
            if not job_list:
                logger.info("No render jobs found")
                return {"job_count": 0, "jobs": []}
            
            jobs = []
            for job in job_list:
                # Get job status
                job_id = job['JobId']
                job_status = current_project.GetRenderJobStatus(job_id)
                
                job_info = {
                    "id": job_id,
                    "name": job.get('TimelineName', 'Unknown'),
                    "status": job_status.get('JobStatus', 'Unknown'),
                    "progress": job_status.get('CompletionPercentage', 0)
                }
                jobs.append(job_info)
            
            logger.info(f"Found {len(jobs)} render jobs")
            
            render_jobs_info = {
                "job_count": len(jobs),
                "jobs": jobs
            }
            
            return render_jobs_info
        
        except Exception as e:
            logger.error(f"Error getting render jobs info: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": f"Error getting render jobs info: {str(e)}"}

def get_resolve_connection():
    """Helper function to get a connection to DaVinci Resolve.
    
    Returns:
        DaVinciResolveAPI or None: API connection if successful, None otherwise
    """
    try:
        logger.info("Attempting to connect to DaVinci Resolve...")
        api = DaVinciResolveAPI()
        status = api.is_resolve_running()
        if status["status"]:
            logger.info(f"Connected to DaVinci Resolve {status['version']}")
            return api
        else:
            logger.error(f"Failed to connect to DaVinci Resolve: {status['error']}")
            return None
    except Exception as e:
        logger.error(f"Error connecting to DaVinci Resolve: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    print("Testing DaVinci Resolve connection...")
    api = get_resolve_connection()
    if api:
        print("Connection successful!")
        project_info = api.get_basic_project_info()
        print("\nCurrent Project Information:")
        print(f"Project Name: {project_info.get('name', 'Unknown')}")
        print(f"Framerate: {project_info.get('framerate', 'Unknown')}")
        print(f"Timeline Count: {project_info.get('timeline_count', 'Unknown')}")
        
        print("\nTesting new API methods:")
        timeline_info = api.get_timeline_info()
        if "error" not in timeline_info:
            print("\nCurrent Timeline Information:")
            print(f"Timeline Name: {timeline_info.get('name', 'Unknown')}")
            print(f"Frames: {timeline_info.get('start_frame', 'Unknown')} - {timeline_info.get('end_frame', 'Unknown')}")
            print(f"Start Timecode: {timeline_info.get('start_timecode', 'Unknown')}")
            print(f"Video Tracks: {timeline_info.get('track_count', {}).get('video', 'Unknown')}")
            print(f"Audio Tracks: {timeline_info.get('track_count', {}).get('audio', 'Unknown')}")
        
        media_pool_info = api.get_media_pool_info()
        if "error" not in media_pool_info:
            print("\nMedia Pool Information:")
            print(f"Root Folder: {media_pool_info.get('root_folder', 'Unknown')}")
            print(f"Current Folder: {media_pool_info.get('current_folder', 'Unknown')}")
            print(f"Selected Clips: {media_pool_info.get('selected_clips', 'Unknown')}")
        
        render_jobs = api.get_render_jobs()
        if "error" not in render_jobs:
            print("\nRender Jobs Information:")
            print(f"Job Count: {render_jobs.get('job_count', 0)}")
            for job in render_jobs.get('jobs', []):
                print(f"  - {job.get('name', 'Unknown')}: {job.get('status', 'Unknown')} ({job.get('progress', 0)}%)")
    else:
        print("Could not connect to DaVinci Resolve. Please check that:")
        print("1. DaVinci Resolve is running")
        print("2. In DaVinci Resolve, go to Preferences -> System -> General and ensure 'External scripting using' is set correctly")
        print("3. The environment variables are correctly set for your operating system")
