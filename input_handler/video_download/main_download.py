import os
import re
import subprocess
import time
import random
import requests
import yt_dlp
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from seleniumwire import webdriver  # Import from seleniumwire
from selenium.webdriver.common.by import By  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.chrome.service import Service  
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.support import expected_conditions as EC  

from loguru import logger

from utils import siginin
from parse_url import get_domain_from_url, parse_youtube_url, decode_url

class VideoDownload():
    def __init__(self):
        self.cloudflare_exceptions = ["tuckercarlson.com"]
        self.SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY")

    def setup_driver(self, url):
        if get_domain_from_url(url) in self.cloudflare_exceptions:
            logger.info("Cloudflare protected")
            options = webdriver.ChromeOptions()
            #user-agent rotation
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
            ]
            #random user agent
            user_agent = random.choice(user_agents)
            #add the user agent
            options.add_argument(f"user-agent={user_agent}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            # options.add_argument("--headless")
            #set up proxy
            proxy_options = {
                "proxy": {
                    "http": f"http://scrapeops.headless_browser_mode=true:{self.SCRAPEOPS_API_KEY}@proxy.scrapeops.io:5353",
                    "https": f"http://scrapeops.headless_browser_mode=true:{self.SCRAPEOPS_API_KEY}@proxy.scrapeops.io:5353",
                    "no_proxy": "localhost:127.0.0.1",
                }
            }
            #disable loading images for faster crawling
            options.add_argument("--blink-settings=imagesEnabled=false")
            #initialize the WebDriver with options
            driver = webdriver.Chrome(options=options, seleniumwire_options=proxy_options)
            return driver
            
        chrome_options = webdriver.ChromeOptions()  
        # chrome_options.add_argument('--headless')  # Run in headless mode (no browser window)  
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36')  
        chrome_options.add_argument('--disable-popup-blocking')  # Disable popup blocks  
        chrome_options.add_argument('--disable-background-timer-throttling')  # Disable background throttling  
        chrome_options.add_argument('--disable-infobars')  # Disable info bars in the UI (e.g., "Chrome is being controlled...")  
        chrome_options.add_argument('--ignore-gpu-blacklist')  # Force enabling GPU even if unsupported by default  
        chrome_options.add_argument('--no-sandbox')  # Bypass OS security model (needed in some environments)  
        chrome_options.add_argument('--disable-dev-shm-usage')  # Prevent crashes due to limited /dev/shm  
        chrome_options.add_argument('--disable-gpu')  # Disable GPU (needed for some rendering issues in headless mode)  
        chrome_options.add_argument('--window-size=1920,1080')  # Set browser window size (needed for responsive web pages)  
        chrome_options.add_argument('--start-maximized')  # Ensure full content is visible  
        chrome_options.add_argument('--disable-extensions')  # Disable extensions for stability  
        
        webdriver_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=webdriver_service, options = chrome_options)
        return driver

    def download_from_youtube(
        self,
        url: str,
        filename: str,
        outdir: str = "output",
    ) -> bool:
        # Clean YouTube URL to keep only video ID
        url_parsed = parse_youtube_url(url)
        logger.info(f"Cleaned YouTube URL: {url_parsed}")

        # Generate output path
        out_path = os.path.join(outdir, filename)
        os.makedirs(outdir, exist_ok=True)

        # Download YouTube audio or live stream with best quality
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": f"{out_path}",
            "quiet": True,
            "sponsorblock-mark": "all",
            "live_from_start": True,  # Start download from the beginning for live streams
        }
        logger.info(f"Full output template: {ydl_opts['outtmpl']}")
        try:
            logger.info("Downloaded")
            logger.info(f"Full output template: {ydl_opts['outtmpl']}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                _ = ydl.extract_info(url_parsed, download=True)
            return True
        except Exception:
            logger.info("Not downloaded")
            return False

    def download_stream(
        self,
        url: str,
        file_name: str,
        dir_data: str,
        media_ext: Optional[str] = None,
        headers: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        logger.info(f"Url='{url}'")

        try:
            # Build headers for ffmpeg command
            header_opts = (
                " ".join(f'-headers "{name}: {value}"' for name, value in headers.items())
                if headers
                else ""
            )

            # Build ffmpeg command
            if media_ext in [".aspx", ".mp3"]:
                # Replace file extension to mp3
                root, _ = os.path.splitext(file_name)
                file_name = f"{root}.mp3"
                file_path = f"{dir_data}/{file_name}"

                # Create FFMPEG command
                user_agent = (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
                )
                ffmpeg_command = (
                    f'ffmpeg -user_agent "{user_agent}" -i "{url}" -c copy -y "{file_path}"'
                )
            else:
                file_path = f"{dir_data}/{file_name}"
                ffmpeg_command = f'ffmpeg {header_opts} -i "{url}" -c copy -bsf:a aac_adtstoasc -y "{file_path}"'
                if "mp3" in url:
                    ffmpeg_command = f'ffmpeg {header_opts} -i "{url}" -c copy -y "{file_path}"'
                if "mp4" or "m3u8" in url:
                    ffmpeg_command = f'ffmpeg {header_opts} -i "{url}" -vn -acodec libmp3lame -q:a 2 -y {file_path}'
            # Run ffmpeg command
            logger.info(f"FFMPEG command: {ffmpeg_command}")
            proc = subprocess.run(
                ffmpeg_command,
                shell=True,
                capture_output=True,
                text=True,
            )

            # Log ffmpeg stdout and stderr
            if proc.stdout:
                logger.info(f"FFMPEG stdout: {proc.stdout}")
            if proc.stderr:
                logger.warning(f"FFMPEG stderr: {proc.stderr}")

            if proc.returncode == 0:
                # Create command for FFPROBE
                ffprobe_command = (
                    "ffprobe -v error -select_streams a -show_entries stream=codec_name "
                    f"-of default=noprint_wrappers=1:nokey=1 {file_path}"
                )

                # Run FFPROBE
                logger.info(f"FFPROBE command: {ffprobe_command}")
                proc = subprocess.run(
                    ffprobe_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                )

                # Log ffprobe stderr
                if proc.stderr:
                    logger.warning(f"FFPROBE stderr: {proc.stderr}")

                # There is some output, meaning there's an audio stream
                if proc.stdout:
                    logger.info(f"FFPROBE stdout: {proc.stdout}")
                    logger.info("Downloaded successfully")
                    return True, file_name
                # No audio stream in the file, delete it
                else:
                    os.remove(file_path)
                    logger.warning("Downloaded file contains no audio")
                    return False, file_name
            else:
                logger.warning("Download failed, ffmpeg command failed")
                return False, file_name

        except Exception as e:
            logger.warning(f"Download failed: {e}")
            return False, file_name

    def download_from_past_stream(
        self,
        driver,
        url: str,
        dir_data: str,
        file_name: str,
    ) -> Tuple[Optional[str], Optional[str]]:

        # Extract domain
        domain = get_domain_from_url(url)
        driver.get(url)
        if domain == "podcasts.apple.com":
            siginin(driver, url, domain)
                # Go to URL


        # driver.get(url)
        time.sleep(10)

        # Live audio scraping
        video_url = driver.current_url
        media_exts = [".mp3", ".wav", ".mp4", ".avi", ".mkv", ".webm", ".aspx"]
        media_ext = os.path.splitext(urlparse(video_url).path)[1]
        if media_ext in media_exts:
            logger.info(f"Direct video url-{video_url}")
            _, file_name = self.download_stream(
                video_url,
                file_name,
                dir_data,
                media_ext,
            )
            return file_name

        else:
            logger.info(f"Not direct video url-{video_url}")
            try:
                video_tag = driver.find_element(By.TAG_NAME, "video")
                logger.info("Found video tag in this page")
                try:
                    video_src = video_tag.find_element(
                        By.TAG_NAME,
                        "source",
                    ).get_attribute("src")

                except Exception:
                    video_src = None

                if video_src is None or video_src == "":
                    video_src = video_tag.get_attribute("src")
                path_url = decode_url(video_src)

                if path_url.endswith(".m3u8"):  # type: ignore
                    logger.info("Found m3u8 in this page")
                    _, file_name = self.download_stream(
                        str(path_url),
                        file_name,
                        dir_data,
                        media_ext,
                    )
                    if is_download_successful:
                        driver.quit()
                        return file_name

                media_ext = os.path.splitext(str(video_src))[1]
                filename_without_ext = os.path.splitext(file_name)[0]
                filename = filename_without_ext + media_ext
                logger.info(f"Found video tags in this page: {video_src}")
                is_download_successful, file_name = self.download_stream(
                    str(video_src),
                    file_name,
                    dir_data,
                    media_ext,
                )
                if is_download_successful:
                    driver.quit()
                    return file_name

            except Exception:
                pass

            try:
                audio_tag = driver.find_element(By.TAG_NAME, "audio")
                logger.info("Found audio tag in this page")
                try:
                    audio_src = audio_tag.find_element(
                        By.TAG_NAME, "source"
                    ).get_attribute("src")
                except Exception:
                    audio_src = None

                if audio_src is None or audio_src == "":
                    audio_src = audio_tag.get_attribute("src")

                path_url = decode_url(audio_src)
                media_ext = os.path.splitext(path_url)[1]

                if path_url.endswith(".m3u8"):  # type: ignore
                    logger.info("Found m3u8 in this page in audio")
                    logger.info(path_url)
                    is_download_successful, file_name = self.download_stream(
                        str(path_url),
                        file_name,
                        dir_data,
                        media_ext,
                    )
                    if is_download_successful:
                        driver.quit()
                        return file_name

                youtube_domains = [
                    "youtube.com",
                    "m.youtube.com",
                    "youtu.be",
                    "bilibili.com",
                ]
                for domain in youtube_domains:
                    if domain in str(audio_src):
                        logger.info("Source identified as YouTube")
                        try:
                            result = self.download_from_youtube(
                                str(audio_src), file_name, dir_data
                            )
                        except Exception as e:
                            logger.info(e)

                        if result == 1:
                            logger.info("Successfully downloaded")
                            driver.quit()
                            return filename
                logger.info(f"Found audio tags in this page: {path_url}")
                is_download_successful, file_name = self.download_stream(
                    path_url,
                    file_name,
                    dir_data,
                    media_ext,
                )
                if is_download_successful:
                    driver.quit()
                    return file_name

                logger.info(f"Found special audio tags in this page: {audio_src}")
                is_download_successful, file_name = self.download_stream(
                    str(audio_src),
                    file_name,
                    dir_data,
                    media_ext,
                )
                if is_download_successful:
                    driver.quit()
                    return file_name
            except Exception:
                pass
            
            print(len(driver.requests)) 
            for request in driver.requests:
                if "kvgo" in domain:
                    mp4_url_pattern = re.compile(
                        r".*\.mp4\?.*Expires=.*", re.IGNORECASE
                    )
                    print("kvgo")
                    if mp4_url_pattern.match(request.url):
                        _, file_name = self.download_stream(
                            request.url,
                            file_name,
                            dir_data,
                            media_ext,
                        )
                        return file_name
                    continue

                if (
                    ("enlivenstream" in domain)
                    or ("vimeo" in domain)
                    or ("sohu" in domain)
                    or ("tenmeetings" in domain)
                ):
                    mp4_url_pattern = re.compile(r".*\.mp4\?.*", re.IGNORECASE)
                    if mp4_url_pattern.match(request.url):
                        print("mp4_url pattern")
                        url = request.url.split(".mp4", 1)[0] + ".mp4"
                        _, file_name = self.download_stream(
                            url,
                            file_name,
                            dir_data,
                            media_ext,
                        )
                        return file_name
                    continue

                if "omnigage" in domain:
                    if "www.omnigage.io/api/" in request.url:
                        res = requests.get(request.url).json()
                        url = (
                            res.get("data")
                            .get("attributes")
                            .get("voice-template-audio-url")
                        )
                        print("omnigage")
                        _, file_name = self.download_stream(
                            url,
                            file_name,
                            dir_data,
                            media_ext,
                        )
                        return file_name

                if "webex" in domain:
                    if "api/v1/recordings" in request.url:
                        res = requests.get(request.url).json()
                        url = (
                            res.get("downloadRecordingInfo")
                            .get("downloadInfo")
                            .get("mp4URL")
                        )
                        print("webex")
                        _, file_name = self.download_stream(
                            url,
                            file_name,
                            dir_data,
                            media_ext,
                        )
                        return file_name

                    else:
                        continue

                if "zoom" in domain:
                    mp4_url_pattern = re.compile(r".*\.mp4\?.*", re.IGNORECASE)

                    if mp4_url_pattern.match(request.url):
                        headers = {key: request.headers[key] for key in request.headers}
                        print("zoom")
                        _, file_name = self.download_stream(
                            request.url,
                            file_name,
                            dir_data,
                            media_ext,
                            headers,
                        )

                        return file_name
                    continue

                if "facebook" in domain or "fb.com" in domain:
                    mp4_url_pattern = re.compile(r".*\.mp4\?.*", re.IGNORECASE)
                    if mp4_url_pattern.match(request.url):
                        headers = {key: request.headers[key] for key in request.headers}
                        url = request.url[: request.url.find("&bytestart")]
                        print("facebook")
                        is_download_successful, file_name = self.download_stream(
                            url,
                            file_name,
                            dir_data,
                            media_ext,
                            headers,
                        )
                        if is_download_successful:
                            return file_name

                # download streams
                if (
                    ".m3u8" in request.url
                    or ".mpd" in request.url
                    or ".ism" in request.url
                    or ".flv" in request.url
                ):
                    url = request.url
                    keys = ["user-agent", "origin", "referer"]
                    headers = {
                        key: request.headers[key]
                        for key in keys
                        if key in request.headers
                    }

                    # Create cookie header
                    if "icastpro" in domain:
                        cookies = driver.get_cookies()
                        cookie = "; ".join(
                            [f"{c.get('name')}={c.get('value')}" for c in cookies]
                        )
                        headers["cookie"] = cookie
                    print("aaaa")
                    is_download_successful, file_name = self.download_stream(
                        url,
                        file_name,
                        dir_data,
                        media_ext,
                        headers,
                    )
                    if is_download_successful:
                        driver.quit()
                        return file_name
        driver.quit()
        return file_name

        # except Exception as e:
        #     logger.warning(f"Error in download_stream: {e}")
        #     return None

    def main(self, url, dir_data, file_name):
        driver = self.setup_driver(url)
        self.download_from_past_stream(driver, url, dir_data, file_name)
        driver.quit()

if __name__ == "__main__":
    # url = "https://podcasts.apple.com/us/podcast/98-red-light-therapy-with-steve-marchese/id1608256407?i=1000670952635"
    # url = "https://thetruthaboutcancer.com/madej-covid-19-transhumanism/"
    # url = "https://rumble.com/v5zdzbb-ana-kasparian-tears-into-democrats-as-charlamagne-nods-in-agreement.html?e9s=src_v1_ucp"
    # url = "https://thehighwire.com/ark-videos/bird-flu-frenzy-fuels-risky-experiments/"
    url = "https://tuckercarlson.com/tucker-show-sachs-3"

    current_directory = os.getcwd()
    video_download = VideoDownload()
    video_download.main(url, dir_data=current_directory, file_name="test.mp3")