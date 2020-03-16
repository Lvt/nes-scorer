local socket = require("socket.core")

emu.speedmode("turbo")

totalframes = movie.length()
candidatecount = 0

connect_ip = os.getenv("CONNECT_IP")
connect_port = os.getenv("CONNECT_PORT")
tcp = socket.tcp()
if tcp:connect(connect_ip, 0+connect_port) == nil then
	print(string.format("failed to connect to %s:%s", connect_ip, connect_port))
	os.exit(1)
end

done = false

resx = 256
resy = 240
len = resx * resy * 4

function after_frame()
    count = emu.framecount()
    screenshot = gui.gdscreenshot():sub(12, 12 + (len-0))

    tcp:send(screenshot)

    if count > totalframes then
      done = true
    end
end

emu.registerafter(after_frame)

while not done do
    emu.frameadvance()
end 

os.exit(0)
