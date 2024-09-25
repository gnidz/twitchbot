import logging
import asyncio
import simpleobsws

logging.basicConfig(level=logging.DEBUG)

parameters = simpleobsws.IdentificationParameters()  # Create an IdentificationParameters object
parameters.eventSubscriptions = (1 << 0) | (1 << 2)  # Subscribe to the General and Scenes categories

ws = simpleobsws.WebSocketClient(url='ws://localhost:4444', password='risBs8nGQX38EpEh',
                                 identification_parameters=parameters)  # WebSocket connection parameters


async def get_scene_item_id(scene_name, source_name):
    response = await ws.call(simpleobsws.Request('GetSceneItemList', {
        'sceneName': scene_name
    }))
    if response.ok():
        for item in response.responseData['sceneItems']:
            if item['sourceName'] == source_name:
                return item['sceneItemId']
    print(f"Source '{source_name}' not found in scene '{scene_name}'.")
    return None


async def toggle_source_visibility(scene_name, source_name, duration=10):
    # Get the sceneItemId for the source
    scene_item_id = await get_scene_item_id(scene_name, source_name)
    if not scene_item_id:
        return

    # Show the source
    await ws.call(simpleobsws.Request('SetSceneItemEnabled', {
        'sceneName': scene_name,
        'sceneItemId': scene_item_id,
        'sceneItemEnabled': True
    }))
    print(f'Source {source_name} is now visible in {scene_name} for {duration} seconds.')

    # Wait for the specified duration
    await asyncio.sleep(duration)

    # Hide the source
    await ws.call(simpleobsws.Request('SetSceneItemEnabled', {
        'sceneName': scene_name,
        'sceneItemId': scene_item_id,
        'sceneItemEnabled': False
    }))
    print(f'Source {source_name} is now hidden in {scene_name}.')


async def init():
    await ws.connect()
    await ws.wait_until_identified()

    # Test: Toggle the visibility of a source for 10 seconds after connecting
    scene_name = "Scene"  # Replace with your scene name
    source_name = "wheel"  # Replace with your source name

    # Start the task to toggle visibility of a source for 10 seconds
    await toggle_source_visibility(scene_name, source_name, 20)


loop = asyncio.get_event_loop()
loop.run_until_complete(init())
loop.run_forever()
