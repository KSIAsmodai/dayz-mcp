modded class MissionGameplay
{
	void ~MissionGameplay()
	{
		MCPClientBridge.ShutdownInstance();
	}

	override void OnMissionStart()
	{
		super.OnMissionStart();

		MCPClientBridge bridge = MCPClientBridge.Get();
		if (bridge)
		{
			bridge.OnTick(0.0);
			bridge.ReleaseGameFocus();
		}
	}

	override void OnUpdate(float timeslice)
	{
		super.OnUpdate(timeslice);

		MCPClientBridge bridge = MCPClientBridge.Get();
		if (bridge)
		{
			bridge.OnTick(timeslice);
		}
	}

	override void OnKeyPress(int key)
	{
		super.OnKeyPress(key);

		MCPClientBridge bridge = MCPClientBridge.Get();
		if (bridge)
		{
			bridge.OnMissionKeyPress(key);
		}
	}
};
