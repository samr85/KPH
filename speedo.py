"""File controlling a 7 segment LCD display for a speedo."""
import scheduler
import sections

# Saved values to display when an update is requested.
SPEEDO_VERSION = 1
SPEEDO_ACTIVE = b""

# Mapping of number to which segments need to be displayed on the 7 segment LCD display
# Yes, I messed up the ordering of the segment pictures...
NUMBERS = {
    0: [1, 3, 2, 5, 4, 7],
    1: [2, 4],
    2: [1, 2, 6, 5, 7],
    3: [1, 2, 6, 4, 7],
    4: [3, 2, 6, 4],
    5: [1, 3, 6, 4, 7],
    6: [1, 3, 6, 4, 5, 7],
    7: [1, 2, 4],
    8: [1, 2, 3, 4, 5, 6, 7],
    9: [1, 3, 2, 6, 4, 7],
}

# Interval to count at in seconds
COUNT_INTERVAL = 60
# Count start point (for testing, should probably be 0 or 1 for main use)
COUNT_OFFSET = 0
# Number to stop counting at
COUNT_TARGET = 88

# Number of times it flashes at the end
FLASHES = 10

# Use this special value to remove the speedo entirely
SPEEDO_OFF = -1
# Use this special value to display a blank speedo
SPEEDO_BLANK = -2


def updateSpeedo(count: int):
    """Display the speedo with the value provided.

    Args:
        count: The value to display.  Must be 0 <= count < 100, SPEEDO_OFF or SPEEDO_BLANK
    """
    global SPEEDO_VERSION, SPEEDO_ACTIVE

    if count == SPEEDO_OFF:
        SPEEDO_ACTIVE = b""
        SPEEDO_VERSION += 1
        sections.pushSection("speedo", 0)
        return

    if count == SPEEDO_BLANK:
        SPEEDO_ACTIVE = b"base"
        SPEEDO_VERSION += 1
        sections.pushSection("speedo", 0)
        return

    if count < SPEEDO_BLANK or count > 100:
        print("Invalid value: %d"%(count))
        return

    active = ["base"]

    digits = map(int, "%02d"%(count,))
    for position, digit in enumerate(digits):
        for number in NUMBERS[digit]:
            active.append("%d%d"%(position+1, number))

    # Update the data that needs to go to each client
    SPEEDO_ACTIVE = (",".join(active)).encode("utf-8")
    # Specify that the SPEEDO_ACTIVE data has changed
    SPEEDO_VERSION += 1
    # Tell clients to request the latest version
    sections.pushSection("speedo", 0)


def startSpeedo():
    for i in range(COUNT_OFFSET, COUNT_TARGET + 1):
        scheduler.runIn(i * COUNT_INTERVAL - COUNT_OFFSET, updateSpeedo, args=(i,))
    for f in range(FLASHES):
        # Blank the speedo half a second after it was last displayed, then turn it back on again half a
        # second after that.  I experimented with other values, but they all looked wrong to me.
        scheduler.runIn(i * COUNT_INTERVAL - COUNT_OFFSET + f + 0.5, updateSpeedo, args=(SPEEDO_BLANK,))
        scheduler.runIn(i * COUNT_INTERVAL - COUNT_OFFSET + f + 1, updateSpeedo, args=(COUNT_TARGET,))


@sections.registerSectionHandler("speedo")
class ExtraDiv(sections.SectionHandler):
    # This is what is called when a team requests the speedo.
    # The requestor variable has the team's object in it, so if you want to do a different thing per team you can use
    # that.
    def requestSection(self, requestor, sectionId):
        return (SPEEDO_VERSION, 0, SPEEDO_ACTIVE)

    def requestUpdateList(self, requestor):
        return [(0, SPEEDO_VERSION)]
