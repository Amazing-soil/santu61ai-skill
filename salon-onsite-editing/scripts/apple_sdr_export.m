#import <Foundation/Foundation.h>
#import <AVFoundation/AVFoundation.h>
int main(int argc,char**argv){@autoreleasepool{
 if(argc!=6){fprintf(stderr,"usage input output start duration preset\n");return 2;}
 AVURLAsset* asset=[AVURLAsset URLAssetWithURL:[NSURL fileURLWithPath:[NSString stringWithUTF8String:argv[1]]] options:nil];
 AVMutableVideoComposition* composition=[AVMutableVideoComposition videoCompositionWithPropertiesOfAsset:asset];
 composition.colorPrimaries=AVVideoColorPrimaries_ITU_R_709_2;
 composition.colorTransferFunction=AVVideoTransferFunction_ITU_R_709_2;
 composition.colorYCbCrMatrix=AVVideoYCbCrMatrix_ITU_R_709_2;
 composition.frameDuration=CMTimeMake(1,30);
 AVAssetExportSession* exporter=[[AVAssetExportSession alloc] initWithAsset:asset presetName:[NSString stringWithUTF8String:argv[5]]];
 exporter.outputURL=[NSURL fileURLWithPath:[NSString stringWithUTF8String:argv[2]]];
 exporter.outputFileType=AVFileTypeMPEG4;
 exporter.videoComposition=composition;
 exporter.timeRange=CMTimeRangeMake(CMTimeMakeWithSeconds(atof(argv[3]),600),CMTimeMakeWithSeconds(atof(argv[4]),600));
 exporter.shouldOptimizeForNetworkUse=YES;
 fprintf(stderr,"render %.0f x %.0f\n",composition.renderSize.width,composition.renderSize.height);
 dispatch_semaphore_t sem=dispatch_semaphore_create(0);
 [exporter exportAsynchronouslyWithCompletionHandler:^{dispatch_semaphore_signal(sem);}];
 dispatch_semaphore_wait(sem,DISPATCH_TIME_FOREVER);
 if(exporter.status!=AVAssetExportSessionStatusCompleted){fprintf(stderr,"export fail %s\n",exporter.error.description.UTF8String);return 1;}
 fprintf(stderr,"native SDR export completed\n");return 0;
}}
