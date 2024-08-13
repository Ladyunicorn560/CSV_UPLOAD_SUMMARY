from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from .forms import UploadFileForm
import pandas as pd
from django.http import HttpResponse

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            
            try:
                # Read the file
                if file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                elif file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    return HttpResponse("Unsupported file format")
                
                # Check if required columns exist
                required_columns = {'Cust State', 'Cust Pin', 'DPD'}
                if not required_columns.issubset(df.columns):
                    return HttpResponse("Required columns are missing in the file")
                
                # Group by Cust State and Cust Pin, then count unique DPD values
                df_grouped = df.groupby(['Cust State', 'Cust Pin'])['DPD'].apply(lambda x: x.unique().tolist()).reset_index()
                
                # Count how many Cust Pins have the same DPD values within each state
                state_pin_dpd_count = df_grouped.groupby('Cust State').apply(
                    lambda group: group.groupby('DPD').size().reset_index(name='Count')
                ).reset_index()
                
                # Count how many Cust Pins have the same DPD values across different states
                pin_dpd_across_states = df_grouped.groupby('Cust Pin')['DPD'].apply(lambda x: ','.join(sorted(set(x)))).reset_index()
                pin_dpd_across_states['States'] = df_grouped.groupby('Cust Pin')['Cust State'].apply(lambda x: ','.join(sorted(set(x)))).values
                pin_dpd_across_states['Count'] = pin_dpd_across_states.groupby('DPD')['Cust Pin'].transform('count')

                # Format the summary report
                summary = "Summary Report\n\n"
                
                summary += "Unique DPD counts within each state:\n"
                for state, group in state_pin_dpd_count.groupby('Cust State'):
                    summary += f"State: {state}\n"
                    for _, row in group.iterrows():
                        summary += f"  DPD Value: {row['DPD']} - Count: {row['Count']}\n"
                    summary += "\n"
                
                summary += "Unique DPD counts across different states:\n"
                for _, row in pin_dpd_across_states.iterrows():
                    summary += f"Cust Pin: {row['Cust Pin']}\n"
                    summary += f"  DPD Values: {row['DPD']}\n"
                    summary += f"  States: {row['States']}\n"
                    summary += f"  Count of Pins with same DPD: {row['Count']}\n\n"

                # Send the summary via email
                send_mail(
                    subject='Python Assignment - Shiksha',
                    message=summary,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=['recipient@example.com'],
                )
                
                return render(request, 'fileupload/success.html', {'summary': summary})
            except Exception as e:
                return HttpResponse(f"An error occurred: {e}")
    else:
        form = UploadFileForm()
    
    return render(request, 'fileupload/upload.html', {'form': form})
