$(document).ready(function(){

    const token = localStorage.getItem('access');
    const $metrics = $('#metrics');

    $metrics.text('Loading metrics...');

    // If user isn't logged in, avoid making a noisy request.
    if (!token) {
        $metrics.text('Login required');
        return;
    }

    $.ajax({
        url:'/api/v1/admin/dashboard/metrics/',
        headers:{
            Authorization:'Bearer ' + token
        },
        success:function(res){

            $('#sales').text(res.total_sales);
            $('#revenue').text(res.total_revenue);
            $('#orders').text(res.active_orders);
            $('#cancelled').text(res.cancel_orders);

            $metrics.text(JSON.stringify(res,null,4));
        },
        error:function(xhr){
            let msg = 'Login required';
            if (xhr && xhr.status && xhr.status !== 401) {
                msg = 'Failed to load metrics (HTTP ' + xhr.status + ')';
            }
            $metrics.text(msg);
        }
    });

});
