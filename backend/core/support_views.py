from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Technician_signup, TechnicianSupportTicket, TechnicianSupportMessage, ServiceRequest
from .support_flow import SUPPORT_CATEGORIES, SUPPORT_TREE
import json

@login_required(login_url='technician_login')
def technician_support_chat(request):
    try:
        technician = Technician_signup.objects.get(user=request.user)
    except Technician_signup.DoesNotExist:
        return redirect('technician_login')
    
    # We will just render the template, React-like logic will be handled via Vanilla JS calling APIs
    return render(request, 'technician/support.html', {'technician': technician})

@login_required
def technician_support_api_action(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        technician = Technician_signup.objects.get(user=request.user)
    except Technician_signup.DoesNotExist:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    data = json.loads(request.body)
    action = data.get('action')
    
    if action == 'INIT':
        # Start a new guided session
        return JsonResponse({
            'message': 'Hi! How can we help you today?',
            'options': SUPPORT_CATEGORIES,
            'state': {'step': 'CATEGORY'}
        })
        
    elif action == 'SELECT':
        selection_id = data.get('selection_id')
        current_state = data.get('state', {})
        step = current_state.get('step')
        
        if step == 'CATEGORY':
            # Technician selected a main category
            node = SUPPORT_TREE.get(selection_id)
            if node:
                current_state['category'] = selection_id
                current_state['step'] = selection_id
                current_state['history'] = [{'q': 'Hi! How can we help you today?', 'a': selection_id}]
                
                return JsonResponse({
                    'message': node.get('question', node.get('text', '')),
                    'options': node.get('options', []),
                    'state': current_state
                })
        
        else:
            # Technician is in the middle of a tree
            node = SUPPORT_TREE.get(step)
            if not node:
                return JsonResponse({'error': 'Invalid state'}, status=400)
            
            # Find the selected option to see the next step
            selected_option = next((opt for opt in node.get('options', []) if opt['id'] == selection_id), None)
            if not selected_option:
                return JsonResponse({'error': 'Invalid option'}, status=400)
                
            history = current_state.get('history', [])
            history.append({'q': node.get('question', node.get('text', '')), 'a': selected_option['label']})
            current_state['history'] = history
            
            if selected_option.get('escalate'):
                # Escalate to admin!
                ticket = TechnicianSupportTicket.objects.create(
                    technician=technician,
                    category=current_state.get('category', 'OTHER'),
                    issue=selected_option.get('label', 'Escalated'),
                    guided_flow_state=current_state
                )
                
                # Format history for admin
                history_text = "GUIDED SUPPORT HISTORY:\n"
                for h in history:
                    history_text += f"- Q: {h['q']}\n  A: {h['a']}\n"
                
                TechnicianSupportMessage.objects.create(
                    ticket=ticket,
                    sender_type='SYSTEM',
                    message=history_text
                )
                
                return JsonResponse({
                    'escalated': True,
                    'ticket_id': ticket.id,
                    'message': 'Your request has been sent to Admin Support. An Admin will respond here shortly.'
                })
                
            next_step_id = selected_option.get('next')
            if not next_step_id:
                 return JsonResponse({'error': 'No next step'}, status=400)
                 
            next_node = SUPPORT_TREE.get(next_step_id)
            current_state['step'] = next_step_id
            
            if next_node.get('end'):
                return JsonResponse({
                    'message': next_node.get('text'),
                    'options': [],
                    'ended': True,
                    'state': current_state
                })
            
            # For intermediate steps
            msg = ""
            if next_node.get('text'):
                msg += next_node['text'] + "\n"
            if next_node.get('question'):
                msg += next_node['question']
                
            return JsonResponse({
                'message': msg.strip(),
                'options': next_node.get('options', []),
                'state': current_state
            })
            
    elif action == 'GET_TICKET_MESSAGES':
        ticket_id = data.get('ticket_id')
        ticket = get_object_or_404(TechnicianSupportTicket, id=ticket_id, technician=technician)
        msgs = ticket.messages.all().order_by('created_at')
        return JsonResponse({
            'messages': [
                {
                    'sender': msg.sender_type,
                    'message': msg.message,
                    'created_at': msg.created_at.strftime("%I:%M %p")
                } for msg in msgs
            ],
            'status': ticket.status
        })

    return JsonResponse({'error': 'Invalid action'}, status=400)

