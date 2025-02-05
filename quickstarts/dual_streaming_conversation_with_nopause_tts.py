import asyncio
import logging
import signal
from dotenv import load_dotenv

# AZURE_SPEECH_KEY =
# AZURE_SPEECH_REGION = "eastus"
# OPENAI_API_KEY =
# NO_PAUSE_API_KEY =
load_dotenv()

from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.streaming.transcriber import *
from vocode.streaming.agent import *
from vocode.streaming.synthesizer import *
from vocode.streaming.models.transcriber import *
from vocode.streaming.models.agent import *
from vocode.streaming.models.synthesizer import *
from vocode.streaming.models.message import BaseMessage


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def main():
    (
        microphone_input,
        speaker_output,
    ) = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=False,
        logger=logger,
        use_blocking_speaker_output=True,  # this moves the playback to a separate thread, set to False to use the main thread
        speaker_sampling_rate=24000,
    )

    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=AzureTranscriber(
            AzureTranscriberConfig.from_input_device(
                microphone_input,
                endpointing_config=PunctuationEndpointingConfig(),
            )
        ),
        agent=ChatGPTAgent(
            ChatGPTAgentConfig(
                initial_message=BaseMessage(text="Hello, how can I help you today?"),
                prompt_preamble="""The AI is having a pleasant conversation about life""",
                dual_stream=True
            )
        ),
        synthesizer=NoPauseSynthesizer(
            NoPauseSynthesizerConfig.from_output_device(speaker_output),
            logger=logger
        ),
        logger=logger,
    )
    await conversation.start()
    print("Conversation started, press Ctrl+C to end")
    signal.signal(
        signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate())
    )
    while conversation.is_active():
        chunk = await microphone_input.get_audio()
        conversation.receive_audio(chunk)


if __name__ == "__main__":
    asyncio.run(main())
