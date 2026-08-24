import re

with open('SevaBandhu-Frontend/templates/customer/dashboard_c.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = re.compile(r'<!-- Support Tickets Panel -->.*?<!-- Activity Stream Panel -->.*?</p>\s*\{% endif %\}\s*</div>', re.DOTALL)
replacement = '''<!-- View All Requests Button -->
            <div class="panel-card" style="display:flex; align-items:center; justify-content:space-between; padding: 24px;">
                <div>
                    <h3 class="panel-title" style="margin-bottom:6px;">My Requests & Support Tickets</h3>
                    <p style="font-size:13px; color:#64748b; margin:0;">View your full booking history, live tracking, and support tickets.</p>
                </div>
                <a href="{% url 'customer_my_requests' %}" class="btn-new-booking" style="background:#0f172a;">
                    View All Requests &rarr;
                </a>
            </div>'''
new_content = target.sub(replacement, content)
if new_content != content:
    with open('SevaBandhu-Frontend/templates/customer/dashboard_c.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Patched dashboard_c.html successfully')
else:
    print('Failed to patch dashboard_c.html. Target pattern not found.')
