with open('SevaBandhu-Frontend/templates/customer/my_requests.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    <!-- List -->
    {% if service_requests %}'''

replacement = '''    <!-- Support Tickets Panel -->
    {% if support_tickets %}
    <div class="req-header-card" style="padding: 20px 32px; margin-bottom: 20px; background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;">
        <h2 style="margin: 0 0 16px 0; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 20px; font-weight: 800; color: #0f172a;">My Support Tickets</h2>
        <div class="requests-grid-list" style="gap: 12px;">
            {% for ticket in support_tickets %}
            <div style="padding: 16px; border: 1px solid #e2e8f0; border-radius: 12px; background: #f8fafc;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <strong style="font-size: 14px; color: #0f172a;">[{{ ticket.ticket_type }}] Ticket #{{ ticket.id }}</strong>
                    <span class="status-tag-pill {% if ticket.status == 'Resolved' %}tag-completed{% else %}tag-assigned{% endif %}">
                        {{ ticket.status }}
                    </span>
                </div>
                <div style="font-size: 13.5px; color: #475569; margin-bottom: 12px;">
                    "{{ ticket.description }}"
                </div>
                {% if ticket.status == 'Resolved' %}
                <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; font-size: 13px; color: #0f172a;">
                    <strong>Admin Response:</strong><br>
                    <span style="color: #334155;">{{ ticket.action_taken }}</span>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <!-- List -->
    {% if service_requests %}'''

new_content = content.replace(target, replacement)
if new_content != content:
    with open('SevaBandhu-Frontend/templates/customer/my_requests.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Patched my_requests.html successfully')
else:
    print('Target not found in my_requests.html')
