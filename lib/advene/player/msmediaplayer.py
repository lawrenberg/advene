"""Windows MediaPlayer interface
"""

import win32com
import win32com.client

class StreamInformation:
    def __init__(self):
        self.streamstatus=None
        self.url=""
        self.position=0
        self.length=0
        
class PositionKeyNotSupported(Exception):
    pass

class PositionOrigin(Exception):
    pass

class InvalidPosition(Exception):
    pass

class PlaylistException(Exception):
    pass

class InternalException(Exception):
    pass

class Player:
    # Class attributes
    AbsolutePosition=0
    RelativePosition=1
    ModuloPosition=2

    ByteCount=0
    SampleCount=1
    MediaTime=2

    # Status
    PlayingStatus=0
    PauseStatus=1
    ForwardStatus=2
    BackwardStatus=3
    InitStatus=4
    EndStatus=5
    UndefinedStatus=6

    # # Exceptions
    # PositionKeyNotSupported=VLC.PositionKeyNotSupported
    # PositionOriginNotSupported=VLC.PositionOriginNotSupported
    # InvalidPosition=VLC.InvalidPosition
    # PlaylistException=VLC.PlaylistException
    # InternalException=VLC.InternalException

    # List of status mappings as defined in
    # http://msdn.microsoft.com/library/default.asp?url=/library/en-us/wmplay/mmp_sdk/playercurrentplaylist.asp
    statusmapping=(UndefinedStatus, EndStatus, PauseStatus, PlayingStatus,
                   ForwardStatus, BackwardStatus, InitStatus, InitStatus,
                   EndStatus, InitStatus, UndefinedStatus, InitStatus)

    # Reference of the MediaPlayer Object Model:
    # http://msdn.microsoft.com/library/default.asp?url=/library/en-us/wmplay/mmp_sdk/controlreference.asp
    def __init__(self):
        # Old version
        #self.player=win32com.client.Dispatch("MediaPlayer.MediaPlayer.1")
        #self.player.AutoSize=1
        #self.player.ShowControls=0
        #self.player.autostart=0
        
        # MediaPlayer9: 
        self.player=win32com.client.Dispatch('{6BF52A52-394A-11d3-B153-00C04F79FAA6}')

        # MediaPlayer Core:
        #w=win32com.client.Dispatch('{09428D37-E0B9-11D2-B147-00C04F79FAA6}')
        #w.launchURL('c:\\windows\\a3dspls.wav')

    def get_media_position(self, origin, key):
        # FIXME
        return 0

    def set_media_position(self, position):
        # FIXME: convert from Position to int.
        # 
        # // Seek to a frame using SMPTE time code.
        # Player.controls.currentPositionTimecode = "[00000]01:00:30.05";
        # current position is in s
        self.player.currentposition=position / 1000.0
        return
    
    def start(self, position):
        self.player.controls.play()

    def pause(self, position):
        self.player.controls.pause()

    def resume(self, position):
        self.player.controls.play()

    def stop(self, position):
        self.player.controls.stop()

    def exit(self):
        # FIXME
        return
    
    def playlist_add_item(self, item):
        # FIXME: we maybe can use .URL
        # Note: convert from dvd://dev/dvd to
        # wmpdvd://drive/title/chapter?contentdir=path
        # (cf http://msdn.microsoft.com/library/default.asp?url=/library/en-us/wmplay/mmp_sdk/wmpdvdprotocol.asp)
        self.player.url=item
        return

    def playlist_clear(self):
        self.player.url=""
        return
        
    def playlist_get_list(self):
        # Could use self.player.playlist property
        return [ self.player.url ]

    def snapshot(self, position):
        # FIXME
        return None

    def all_snapshots(self):
        # FIXME
        pass
    
    def display_text (self, message, begin, end):
        # Use self.closedCaption object and generate SAMI captions
        # http://msdn.microsoft.com/library/en-us/wmplay/mmp_sdk/playerclosedcaption.asp?frame=true
        # Maybe use a UTBV to generate SAMI because we must give a SMI URL
        
        pass

    def get_stream_information(self):
        s=StreamInformation()
        s.url=self.player.FileName
        s.length=self.player.duration
        s.position=self.player.currentposition
        # For status list:
        # http://msdn.microsoft.com/library/default.asp?url=/library/en-us/wmplay/mmp_sdk/playercurrentplaylist.asp
        s.streamstatus=statusmapping[self.player.playstate]
        # FIXME
        pass
        
    def sound_get_volume(self):
        # FIXME: Normalize volume to be in [0..255]
        return self.player.volume

    def sound_set_volume(self, v):
        # FIXME: Normalize volume to be in [0..255]
        self.player.volume=v

        
        
