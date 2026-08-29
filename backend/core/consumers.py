import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class RequestConsumer(AsyncJsonWebsocketConsumer):

    #########################################################
    # CONNECT
    #########################################################

    async def connect(self):

        print("[ICON] SOCKET CONNECTED")

        #################################################
        # TECHNICIAN GROUP
        #################################################

        self.group_name = 'technicians'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        #################################################
        # REQUEST-SPECIFIC TRACKING GROUP
        #################################################

        self.request_id = self.scope['url_route']['kwargs'].get('id')

        if self.request_id:

            self.tracking_group_name = f"tracking_{self.request_id}"

            await self.channel_layer.group_add(
                self.tracking_group_name,
                self.channel_name
            )

        #################################################
        # ACCEPT SOCKET
        #################################################

        await self.accept()

        #################################################
        # SEND CONNECT MESSAGE
        #################################################

        await self.send(text_data=json.dumps({
            'message': 'Connected'
        }))

    #########################################################
    # DISCONNECT
    #########################################################

    async def disconnect(self, close_code):

        print("[ICON] SOCKET DISCONNECTED")

        #################################################
        # REMOVE TECHNICIAN GROUP
        #################################################

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        #################################################
        # REMOVE TRACKING GROUP
        #################################################

        if hasattr(self, 'tracking_group_name'):

            await self.channel_layer.group_discard(
                self.tracking_group_name,
                self.channel_name
            )

    

    #########################################################
    # NEW REQUEST NOTIFICATION
    #########################################################

    async def new_request(self, event):

        print("[FIRE] CONSUMER RECEIVED EVENT")

        await self.send(text_data=json.dumps(
            event['content']
        ))

    #########################################################
    # REMOVE NOTIFICATION
    #########################################################

    async def notification_removed(self, event):

        print("[FIRE] notification_removed HIT")

        await self.send(text_data=json.dumps({
            'type': 'notification_removed',
            'request_id': event['request_id']
        }))

    #########################################################
    # TECHNICIAN MESSAGE
    #########################################################

    async def technicians_message(self, event):

        await self.send_json(event['content'])

    #########################################################
    # RECEIVE LIVE GPS
    #########################################################

    async def receive(self, text_data):

        data = json.loads(text_data)

        print("[ICON] RECEIVED:", data)

        #################################################
        # LIVE LOCATION TRACKING
        ##################################
        if data.get('type') == 'live_location':

            latitude = data.get('latitude')
            longitude = data.get('longitude')
            request_id = data.get('request_id')

            print(
                "[ICON] LIVE GPS:",
                latitude,
                longitude,
                "REQUEST:",
                request_id
            )

            #################################################
            # SEND TO REQUEST-SPECIFIC TRACKING GROUP
            #################################################

            if request_id:

                await self.channel_layer.group_send(

                    f"tracking_{request_id}",

                    {
                        'type': 'location_update',

                        'latitude': latitude,
                        'longitude': longitude,
                    }
                )

    #########################################################
    # SEND LIVE LOCATION TO CUSTOMER
    #########################################################

    async def location_update(self, event):

        await self.send(text_data=json.dumps({

            'type': 'location_update',

            'latitude': event['latitude'],
            'longitude': event['longitude'],

        }))

from channels.db import database_sync_to_async

class ChatConsumer(AsyncJsonWebsocketConsumer):
    
    @database_sync_to_async
    def get_service_request(self, request_id):
        from core.models import ServiceRequest
        try:
            return ServiceRequest.objects.get(id=request_id)
        except ServiceRequest.DoesNotExist:
            return None

    @database_sync_to_async
    def get_user_role_and_verify(self, user, service_request):
        # Determine if the user is the customer or technician for this request
        if user.username == service_request.customer_username:
            return 'customer'
        elif user.username == service_request.technician_username:
            return 'technician'
        return None
        
    @database_sync_to_async
    def get_chat_conversation(self, service_request):
        from core.models import ChatConversation
        try:
            return ChatConversation.objects.get(service_request=service_request)
        except ChatConversation.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, conversation, sender_username, message_text):
        from core.models import ChatMessage
        msg = ChatMessage.objects.create(
            conversation=conversation,
            sender_username=sender_username,
            message=message_text
        )
        return msg

    async def connect(self):
        print("[CHAT] SOCKET CONNECTED")
        
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            print("[CHAT] User not authenticated")
            await self.close()
            return

        self.request_id = self.scope['url_route']['kwargs'].get('request_id')
        if not self.request_id:
            print("[CHAT] No request ID")
            await self.close()
            return

        self.service_request = await self.get_service_request(self.request_id)
        if not self.service_request:
            print("[CHAT] ServiceRequest not found")
            await self.close()
            return

        self.role = await self.get_user_role_and_verify(self.user, self.service_request)
        if not self.role:
            print("[CHAT] User not authorized for this request")
            await self.close()
            return

        if self.service_request.status == 'Pending':
            print("[CHAT] Request is Pending, chat not allowed")
            await self.close()
            return

        if self.service_request.status == 'Assigned' and not getattr(self.service_request, 'tracking_active', False):
            print("[CHAT] Journey not started, chat not allowed")
            await self.close()
            return

        self.conversation = await self.get_chat_conversation(self.service_request)
        if not self.conversation:
            print("[CHAT] Conversation not found")
            await self.close()
            return

        self.chat_group_name = f"chat_{self.request_id}"

        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )

        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': 'Connected to chat'
        }))

    async def disconnect(self, close_code):
        print("[CHAT] SOCKET DISCONNECTED")
        if hasattr(self, 'chat_group_name'):
            await self.channel_layer.group_discard(
                self.chat_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            # Refresh service request to check status
            self.service_request = await self.get_service_request(self.request_id)
            if self.service_request.status == 'Completed':
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Chat is closed. Service is completed.'
                }))
                return
                
            if self.service_request.status == 'Assigned' and not getattr(self.service_request, 'tracking_active', False):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Chat is unavailable until journey starts.'
                }))
                return

            self.conversation = await self.get_chat_conversation(self.service_request)
            if not self.conversation or not self.conversation.is_active:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Chat conversation is not active.'
                }))
                return

            message_text = data.get('message', '').strip()
            if not message_text:
                return

            # Ensure sender is derived from self.scope['user'] server-side
            sender_username = self.user.username

            msg = await self.save_message(self.conversation, sender_username, message_text)

            # Broadcast message to room group
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'sender_username': sender_username,
                    'message': message_text,
                    'created_at': msg.created_at.isoformat()
                }
            )

    async def chat_message_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'sender_username': event['sender_username'],
            'message': event['message'],
            'created_at': event['created_at']
        }))