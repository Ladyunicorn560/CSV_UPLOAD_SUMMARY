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
                
                # Compute required metrics
                cust_state_count = df['Cust State'].nunique()
                cust_pin_count = df['Cust Pin'].nunique()
                dpd_count = df['DPD'].nunique()
                
                summary = (
                    f"Total Unique Cust States: {cust_state_count}\n"
                    f"Total Unique Cust Pins: {cust_pin_count}\n"
                    f"Total Unique DPD Values: {dpd_count}\n\n"
                )
                
                # Additional detailed information
                state_pin_count = df.groupby('Cust State')['Cust Pin'].nunique().to_string()
                dpd_per_state = df.groupby('Cust State')['DPD'].nunique().to_string()

                summary += (
                    "Unique Cust Pins per Cust State:\n" + state_pin_count + "\n\n"
                    "Unique DPD per Cust State:\n" + dpd_per_state
                )
                
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

